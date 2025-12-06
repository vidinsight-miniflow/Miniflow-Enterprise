from typing import Any, Dict, Generic, List, Optional, TypeVar, cast, Callable, Tuple, Union
from sqlalchemy import select, func, exists, or_
from sqlalchemy.orm import DeclarativeMeta, Session
from sqlalchemy.sql import Select
from sqlalchemy.exc import (
    SQLAlchemyError, 
    IntegrityError, 
    OperationalError,
    DataError,
    ProgrammingError,
    InvalidRequestError,
    TimeoutError as SQLAlchemyTimeoutError
)
from datetime import datetime, timezone
from functools import wraps

from ..database.utils.filter_params import FilterParams
from ..database.utils.pagination_params import PaginationParams, PaginatedResponse, PaginationMetadata
from ..core.exceptions import (
    AppException,
    DatabaseQueryError,
    DatabaseValidationError,
    DatabaseConnectionError,
    DatabaseSessionError,
    ResourceNotFoundError,
)


# Type variables
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: ModelType):
        self.model = model
        self.model_name = model.__name__

    @staticmethod
    def _handle_db_exceptions(func: Callable) -> Callable:
        """
        Veritabanı hatalarını yakalayıp özel exception'lara dönüştüren dekoratör.
        
        Bu dekoratör tüm repository metodlarına sarılır ve SQLAlchemy exception'larını
        yakalayıp anlamlı, özel DatabaseError alt sınıflarına dönüştürür. Her hata tipi
        için uygun error code ve severity level atar. Exception chaining ile original
        hatayı korur, böylece debugging kolaylaşır.
        
        Args:
            func (Callable): Dekore edilecek fonksiyon (repository metodu)
            
        Returns:
            Callable: Exception handling ile sarılmış fonksiyon
            
        Raises:
            DatabaseValidationError: Integrity constraint ihlalleri için
                - Unique constraint ihlali (UNIQUE_CONSTRAINT_VIOLATION)
                - Foreign key constraint ihlali (FOREIGN_KEY_VIOLATION)
                - Not null constraint ihlali (NOT_NULL_VIOLATION)
                - Check constraint ihlali (CHECK_CONSTRAINT_VIOLATION)
                Severity: MEDIUM
            
            DatabaseQueryError: Veri ve SQL hataları için
                - DataError: Yanlış veri tipi, aralık dışı değer (DATA_ERROR)
                  Severity: MEDIUM
                - ProgrammingError: SQL syntax hatası, tablo/kolon bulunamadı (QUERY_ERROR)
                  Severity: HIGH
                - OperationalError: Transaction hatası, database erişim hatası (OPERATIONAL_ERROR)
                  Severity: HIGH
            
            DatabaseConnectionError: Bağlantı ve timeout sorunları için
                - TimeoutError: Query/connection timeout (CONNECTION_TIMEOUT)
                  Severity: CRITICAL
            
            DatabaseSessionError: Session yönetim hataları için
                - InvalidRequestError: Session kapalı, geçersiz işlem (INVALID_SESSION)
                  Severity: HIGH
            
            DatabaseError: Diğer tüm SQLAlchemy hataları için
                - SQLAlchemyError: Kategorize edilemeyen hatalar (DATABASE_ERROR)
                  Severity: HIGH
        
        Exception Dönüşüm Akışı:
            1. IntegrityError yakalanır
               → error mesajı analiz edilir (unique, foreign key, not null)
               → DatabaseValidationError(error_code, MEDIUM) oluşturulur
               → 'from e' ile original exception chain'lenir
            
            2. DataError yakalanır
               → DatabaseQueryError(DATA_ERROR, MEDIUM) oluşturulur
            
            3. ProgrammingError yakalanır
               → DatabaseQueryError(QUERY_ERROR, HIGH) oluşturulur
            
            4. OperationalError yakalanır
               → DatabaseQueryError(OPERATIONAL_ERROR, HIGH) oluşturulur
            
            5. TimeoutError yakalanır
               → DatabaseConnectionError(CONNECTION_TIMEOUT, CRITICAL) oluşturulur
            
            6. InvalidRequestError yakalanır
               → DatabaseSessionError(INVALID_SESSION, HIGH) oluşturulur
            
            7. SQLAlchemyError (catch-all) yakalanır
               → DatabaseError(DATABASE_ERROR, HIGH) oluşturulur
        
        Error Code Belirleme Logic (IntegrityError için):
            - "unique" in error_msg → UNIQUE_CONSTRAINT_VIOLATION
            - "foreign key" in error_msg → FOREIGN_KEY_VIOLATION
            - "not null" in error_msg → NOT_NULL_VIOLATION
            - "check constraint" in error_msg → CHECK_CONSTRAINT_VIOLATION
            - Diğer → CONSTRAINT_VIOLATION (genel)
        
        Examples:
            >>> # Dekoratör otomatik olarak tüm metodlara uygulanır
            >>> @_handle_db_exceptions
            >>> def _create(self, session, **kwargs):
            ...     obj = self.model(**kwargs)
            ...     session.add(obj)
            ...     session.flush()  # IntegrityError fırlatabilir
            ...     return obj
            
            >>> # Kullanım: Unique constraint ihlali
            >>> try:
            ...     user = user_repo._create(
            ...         session,
            ...         email="existing@example.com"  # Bu email zaten var
            ...     )
            ... except DatabaseValidationError as e:
            ...     print(f"Hata: {e.error_message}")
            ...     # "Failed to create User: Unique constraint violation"
            ...     print(f"Error Code: {e.error_code}")
            ...     # ErrorCode.UNIQUE_CONSTRAINT_VIOLATION
            ...     print(f"Severity: {e.error_severity}")
            ...     # ErrorSeverity.MEDIUM
            ...     print(f"Original: {e.__cause__}")
            ...     # IntegrityError(...)
            
            >>> # Foreign key violation
            >>> try:
            ...     post = post_repo._create(
            ...         session,
            ...         title="Test",
            ...         user_id="non_existent_user"  # Bu user yok
            ...     )
            ... except DatabaseValidationError as e:
            ...     print(e.error_code)  # FOREIGN_KEY_VIOLATION
            
            >>> # Connection timeout
            >>> try:
            ...     users = user_repo._get_all(session)
            ... except DatabaseConnectionError as e:
            ...     print(e.error_severity)  # CRITICAL
            ...     # Retry logic tetiklenebilir
        
        Note:
            - functools.wraps ile fonksiyon metadata'sı korunur (__name__, __doc__ vb.)
            - Exception chaining ('from e') sayesinde original hataya __cause__ ile erişilir
            - self.model_name error mesajlarına otomatik eklenir
            - Tüm custom exception'lar DatabaseError base class'ından türer
            - Error severity level'lar otomatik atanır ve loglama için kullanılabilir
            - Exception mesajları İngilizce'dir (API response için)
        
        Technical Details:
            - Decorator pattern kullanır (higher-order function)
            - Inner wrapper fonksiyonu closure oluşturur
            - *args, **kwargs ile generic wrapper (tüm metodlara uygulanabilir)
            - Exception hierarchy: spesifikten genel'e doğru kontrol edilir
            - Original exception her zaman __cause__ attribute'unda saklanır
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            """
            Dekoratör wrapper fonksiyonu - exception handling logic'ini içerir.
            
            Bu inner fonksiyon gerçek exception handling implementasyonunu içerir.
            Dekore edilen fonksiyonu try-except bloğu içinde çalıştırır ve tüm
            SQLAlchemy exception'larını yakalar, analiz eder ve uygun custom
            exception'lara dönüştürür. Exception chaining ile original hatayı korur.
            
            Wrapper Çalışma Akışı:
                1. func(self, *args, **kwargs) çağrılır
                2. Eğer başarılı ise sonuç direkt döndürülür
                3. Eğer exception fırlatılırsa:
                   a. Exception tipi kontrol edilir (spesifikten genel'e)
                   b. Uygun custom exception oluşturulur
                   c. Error message self.model_name ile zenginleştirilir
                   d. 'from e' ile original exception chain'lenir
                   e. Custom exception fırlatılır (raise ... from e)
            
            Args:
                self (BaseRepository): Repository instance (model_name'e erişim için)
                *args (Any): Dekore edilen fonksiyonun positional argümanları
                    Örnek: session, record_id, filter_params vb.
                **kwargs (Any): Dekore edilen fonksiyonun keyword argümanları
                    Örnek: created_by="user_id", is_active=True vb.
            
            Returns:
                Any: Dekore edilen fonksiyonun döndürdüğü değer
                    - ModelType: Tek model instance (_get_by_id, _create, _update vb.)
                    - List[ModelType]: Model listesi (_get_all, _filter vb.)
                    - Optional[ModelType]: None veya model (_get_first, _get_last vb.)
                    - Tuple[ModelType, bool]: (_get_or_create, _upsert için)
                    - PaginatedResponse[ModelType]: (_paginate için)
                    - int: Sayaç (_count için)
                    - bool: Boolean (_exists için)
            
            Raises:
                DatabaseValidationError: IntegrityError yakalandığında
                    Error code determination:
                    - error_msg.lower() içinde "unique" varsa → UNIQUE_CONSTRAINT_VIOLATION
                    - error_msg.lower() içinde "foreign key" varsa → FOREIGN_KEY_VIOLATION
                    - error_msg.lower() içinde "not null" varsa → NOT_NULL_VIOLATION
                    - error_msg.lower() içinde "check constraint" varsa → CHECK_CONSTRAINT_VIOLATION
                    - Hiçbiri yoksa → CONSTRAINT_VIOLATION (fallback)
                    Error message format: f"Failed to perform operation on {self.model_name}: {error description}"
                    Severity: MEDIUM (her zaman)
                
                DatabaseQueryError: DataError, ProgrammingError veya OperationalError yakalandığında
                    - DataError → error_code=DATA_ERROR, severity=MEDIUM
                      Örnek: "Invalid data type for column", "Numeric value out of range"
                    - ProgrammingError → error_code=QUERY_ERROR, severity=HIGH
                      Örnek: "Syntax error in SQL", "Table/column doesn't exist"
                    - OperationalError → error_code=OPERATIONAL_ERROR, severity=HIGH
                      Örnek: "Database connection lost", "Transaction failed"
                    Error message format: f"Failed to query {self.model_name}: {original error}"
                
                DatabaseConnectionError: TimeoutError yakalandığında
                    Error code: CONNECTION_TIMEOUT
                    Severity: CRITICAL (en yüksek seviye - immediate action gerekir)
                    Error message format: f"Connection timeout while accessing {self.model_name}: {details}"
                    Kullanım: Retry logic, circuit breaker pattern tetiklemek için
                
                DatabaseSessionError: InvalidRequestError yakalandığında
                    Error code: INVALID_SESSION
                    Severity: HIGH
                    Error message format: f"Invalid session request for {self.model_name}: {reason}"
                    Nedenler: Session closed, detached instance, invalid state
                
                DatabaseError: SQLAlchemyError (catch-all) yakalandığında
                    Error code: DATABASE_ERROR
                    Severity: HIGH
                    Error message format: f"Database error for {self.model_name}: {error}"
                    Bu: Yukarıdaki kategorilere girmeyen tüm SQLAlchemy hataları için
            
            Exception Handling Sequence (try-except blokları sırası önemli):
                1. IntegrityError → En spesifik, constraint ihlalleri
                2. DataError → Veri tipi/format hataları
                3. ProgrammingError → SQL syntax, schema hataları
                4. OperationalError → Database operational sorunları
                5. TimeoutError → Connection/query timeout
                6. InvalidRequestError → Session management hataları
                7. SQLAlchemyError → Catch-all (en genel)
            
            Exception Chaining Details:
                - 'raise CustomException(...) from e' syntax kullanılır
                - Original exception e.__cause__ attribute'unda saklanır
                - Traceback zinciri korunur (debugging için kritik)
                - Custom exception message user-friendly, __cause__ technical details içerir
            
            Examples:
                >>> # Unique constraint violation örneği
                >>> @_handle_db_exceptions
                >>> def _create(self, session, **kwargs):
                ...     obj = self.model(**kwargs)
                ...     session.add(obj)
                ...     session.flush()  # IntegrityError: duplicate key
                ...     return obj
                >>> 
                >>> # Wrapper'ın yapacağı:
                >>> # 1. func çağrılır: _create(repo, session, email="test@test.com")
                >>> # 2. flush() IntegrityError fırlatır
                >>> # 3. except IntegrityError as e: bloğu yakalar
                >>> # 4. error_msg = str(e).lower() analiz edilir
                >>> # 5. "unique" kelimesi bulunur
                >>> # 6. DatabaseValidationError oluşturulur:
                >>> #    error_message="Failed to perform operation on User: Unique constraint violation"
                >>> #    error_code=UNIQUE_CONSTRAINT_VIOLATION
                >>> #    error_severity=MEDIUM
                >>> # 7. raise DatabaseValidationError(...) from e
                >>> # 8. Caller tarafında:
                >>> try:
                ...     user = repo._create(session, email="existing@test.com")
                ... except DatabaseValidationError as ex:
                ...     print(ex.error_message)  # User-friendly
                ...     print(ex.__cause__)  # Original IntegrityError (debugging için)
            
            Note:
                - Wrapper self'e erişebilir (closure): self.model_name kullanır
                - functools.wraps decorator'ı metadata'yı korur:
                  * func.__name__ → wrapper.__name__
                  * func.__doc__ → wrapper.__doc__
                  * func.__module__ → wrapper.__module__
                - *args/**kwargs ile generic: Her fonksiyon signature'ına uyar
                - Exception order önemli: Spesifikten genel'e (IntegrityError → SQLAlchemyError)
                - Her custom exception original exception'ı chain'ler (debugging için)
            
            Performance Impact:
                - Minimal overhead: Sadece exception durumunda extra processing
                - Normal flow'da: Tek bir function call overhead (negligible)
                - Exception durumunda: String processing + exception instantiation
                - Trade-off: Tiny performance cost vs. huge maintainability gain
            
            Best Practices Applied:
                - Exception chaining: Debugging bilgisini kaybetmez
                - Spesifik exceptions: Caller'lar farklı hataları farklı handle edebilir
                - Consistent error format: Tüm error mesajları model_name içerir
                - Severity levels: Loglama ve alerting için kullanılabilir
                - Error codes: Programmatic error handling için (if error_code == ...)
            """
            try:
                return func(self, *args, **kwargs)
            
            except IntegrityError as e:
                # Handle constraint violations (unique, foreign key, not null, etc.)
                raise DatabaseValidationError() from e
            
            except DataError as e:
                # Handle data type errors (invalid data format, out of range, etc.)
                raise DatabaseQueryError() from e
            
            except ProgrammingError as e:
                # Handle SQL syntax errors, missing tables/columns, etc.
                raise DatabaseQueryError() from e
            
            except OperationalError as e:
                # Handle database connection issues, transaction errors, etc.
                raise DatabaseConnectionError() from e
            
            except SQLAlchemyTimeoutError as e:
                # Handle timeout errors
                raise DatabaseConnectionError() from e
            
            except InvalidRequestError as e:
                # Handle invalid session state or request errors
                raise DatabaseSessionError() from e
            
            except AppException:
                # Re-raise AppException and its subclasses (ResourceNotFoundError, DatabaseValidationError, etc.)
                # These should be handled by the exception handler, not converted to DatabaseQueryError
                raise
            
            except SQLAlchemyError as e:
                # Catch-all for any other SQLAlchemy errors
                raise DatabaseQueryError() from e
            
            except Exception as e:
                # Catch-all for unexpected errors
                raise DatabaseQueryError() from e
        
        return wrapper

    def _raise_not_found_error(self, record_id: str) -> None:
        """
        Kayıt bulunamadığında ResourceNotFoundError fırlatır.
        
        Bu yardımcı fonksiyon, bir kayıt bulunamadığında tutarlı bir şekilde
        hata fırlatmak için kullanılır. Model adını otomatik olarak resource_name
        olarak kullanır.
        
        Args:
            record_id (str): Bulunamayan kaydın ID'si
        
        Raises:
            ResourceNotFoundError: Her zaman fırlatılır
                - resource_name: Model adı (örn: "User", "AgreementVersion")
                - resource_id: record_id
        
        Examples:
            >>> # _get_by_id içinde kullanım
            >>> def _get_by_id(self, session, record_id, raise_not_found=True):
            ...     result = session.get(self.model, record_id)
            ...     if result is None and raise_not_found:
            ...         self._raise_not_found_error(record_id)  # Tutarlı hata
            ...     return result
            
            >>> # Caller tarafında yakalama
            >>> try:
            ...     user = user_repo._get_by_id(session, "non_existent_id")
            ... except ResourceNotFoundError as e:
            ...     print(e.resource_name)  # "User"
            ...     print(e.resource_id)  # "non_existent_id"
        
        Note:
            - Bu fonksiyon direkt çağrılmaz, internal kullanım içindir
            - Model adı resource_name olarak kullanılır
        """
        raise ResourceNotFoundError(
            resource_name=self.model_name,
            resource_id=record_id
        )

    def _apply_filters(self, query: Select, filter_params: Optional[FilterParams] = None) -> Select:
        """
        FilterParams'dan gelişmiş filtreleri sorguya uygular.
        
        Bu yardımcı fonksiyon, karmaşık filtreleme operatörlerini (>, <, IN, LIKE vb.)
        SQLAlchemy query'sine çevirir. 12 farklı operatör + search desteği vardır.
        
        Args:
            query (Select): Filtre uygulanacak SQLAlchemy select query
            filter_params (Optional[FilterParams]): Filtre parametreleri
                - filters: Dict[str, Any] - Alan adı ve değerleri
                - operators: Dict[str, str] - Her alan için operatör (varsayılan: "eq")
                - search: Optional[str] - Arama terimi
                - search_fields: List[str] - Aranacak alanlar
        
        Returns:
            Select: Filtrelenmiş SQLAlchemy query
        
        Desteklenen Operatörler:
            - eq: Eşittir (field == value)
            - ne: Eşit değildir (field != value)
            - gt: Büyüktür (field > value)
            - gte: Büyük veya eşittir (field >= value)
            - lt: Küçüktür (field < value)
            - lte: Küçük veya eşittir (field <= value)
            - in: İçinde (field IN [value1, value2, ...])
            - like: SQL LIKE (case-sensitive) (field LIKE '%value%')
            - ilike: SQL ILIKE (case-insensitive) (field ILIKE '%value%')
            - is_null: NULL kontrolü (field IS NULL)
            - is_not_null: NULL değil kontrolü (field IS NOT NULL)
        
        Çalışma Mantığı:
            1. filter_params boş veya filtre yoksa → query'yi olduğu gibi döndür
            2. Her filter için:
               a. Model'de alan var mı kontrol et
               b. Operator'ü al (varsayılan: "eq")
               c. Operator'e göre WHERE koşulu ekle
               d. Geçersiz alan/operator için print warning
            3. Search varsa:
               a. search_fields'daki her alan için ILIKE koşulu oluştur
               b. OR ile birleştir (herhangi biri match etsins)
               c. Query'ye ekle
        
        Examples:
            >>> # Yaş aralığı filtresi
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gte")
            >>> filter_params.add_filter("age", 65, "lte")
            >>> query = select(User)
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE age >= 18 AND age <= 65
            
            >>> # IN operatörü
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("status", ["active", "pending"], "in")
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE status IN ('active', 'pending')
            
            >>> # LIKE arama (case-sensitive)
            >>> filter_params = FilterParams()
            >>> filter_params.add_like_filter("email", "%@gmail.com%", case_sensitive=True)
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE email LIKE '%@gmail.com%'
            
            >>> # ILIKE arama (case-insensitive)
            >>> filter_params = FilterParams()
            >>> filter_params.add_like_filter("name", "%john%", case_sensitive=False)
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE name ILIKE '%john%'
            
            >>> # NULL kontrolü
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("deleted_at", None, "is_null")
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE deleted_at IS NULL
            
            >>> # Search (multiple fields)
            >>> filter_params = FilterParams()
            >>> filter_params.search = "john"
            >>> filter_params.search_fields = ["name", "email", "username"]
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE (name ILIKE '%john%' OR email ILIKE '%john%' OR username ILIKE '%john%')
            
            >>> # Kombine filtreler
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gte")
            >>> filter_params.add_filter("is_active", True, "eq")
            >>> filter_params.search = "john"
            >>> filter_params.search_fields = ["name", "email"]
            >>> query = self._apply_filters(query, filter_params)
            >>> # WHERE age >= 18 AND is_active = True AND (name ILIKE '%john%' OR email ILIKE '%john%')
        
        Note:
            - Geçersiz alan adları için print warning verir (exception fırlatmaz)
            - Geçersiz operatörler için print warning verir ve atlanır
            - Search koşulları OR ile birleştirilir (geniş arama)
            - Filter koşulları AND ile birleştirilir (dar arama)
            - Search her zaman case-insensitive'dir (ILIKE kullanır)
            - Model'de olmayan alanlar sessizce atlanır
        
        Warning:
            LIKE/ILIKE kullanırken % wildcard'ı value'ye dahil edilmelidir!
            Örnek: "%gmail%" (başta ve sonda %)
        """
        if not filter_params or not filter_params.has_filters():
            return query

        # Apply field filters with operators
        for key, value in filter_params.filters.items():
            if not hasattr(self.model, key):
                print(f"Attempted to filter by non-existent field '{key}' on {self.model_name}")
                continue

            field = getattr(self.model, key)
            operator = filter_params.operators.get(key, "eq")

            if operator == "eq":
                query = query.where(field == value)
            elif operator == "ne":
                query = query.where(field != value)
            elif operator == "gt":
                query = query.where(field > value)
            elif operator == "gte":
                query = query.where(field >= value)
            elif operator == "lt":
                query = query.where(field < value)
            elif operator == "lte":
                query = query.where(field <= value)
            elif operator == "in":
                query = query.where(field.in_(value))
            elif operator == "like":
                query = query.where(field.like(value))
            elif operator == "ilike":
                query = query.where(field.ilike(value))
            elif operator == "is_null":
                query = query.where(field.is_(None))
            elif operator == "is_not_null":
                query = query.where(field.isnot(None))
            else:
                print(f"Unknown operator '{operator}' for field '{key}' on {self.model_name}")

        # Apply search filters (outside the loop to avoid duplication)
        if filter_params.search and filter_params.search_fields:
            search_conditions = []
            for field_name in filter_params.search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.ilike(f"%{filter_params.search}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        return query

    def _apply_simple_filters(self, query: Select, **filters) -> Select:
        """
        Basit eşitlik filtrelerini sorguya uygular.
        
        Bu yardımcı fonksiyon, sadece eşitlik (==) kontrolü yapar. Karmaşık
        operatörler için _apply_filters() kullanılmalıdır. Performanslı ve basit.
        
        Args:
            query (Select): Filtre uygulanacak SQLAlchemy select query
            **filters (Any): Keyword arguments olarak filtreler
                Örnek: is_active=True, role="admin", age=30
        
        Returns:
            Select: Filtrelenmiş SQLAlchemy query
        
        Çalışma Mantığı:
            1. Her filter için (key=value):
               a. Model'de key alanı var mı kontrol et
               b. Varsa: WHERE key == value ekle
               c. Yoksa: Print warning ver ve atla
            2. Filtrelenmiş query'yi döndür
        
        Examples:
            >>> # Tek filtre
            >>> query = select(User)
            >>> query = self._apply_simple_filters(query, is_active=True)
            >>> # WHERE is_active = True
            
            >>> # Çoklu filtre
            >>> query = select(User)
            >>> query = self._apply_simple_filters(
            ...     query,
            ...     is_active=True,
            ...     role="admin",
            ...     email_verified=True
            ... )
            >>> # WHERE is_active = True AND role = 'admin' AND email_verified = True
            
            >>> # None değer kontrolü
            >>> query = select(User)
            >>> query = self._apply_simple_filters(query, deleted_at=None)
            >>> # WHERE deleted_at IS NULL (SQLAlchemy otomatik çevirir)
            
            >>> # _get_all metodunda kullanım
            >>> def _get_all(self, session, **filters):
            ...     query = select(self.model)
            ...     query = self._apply_simple_filters(query, **filters)
            ...     return session.execute(query).scalars().all()
            >>> 
            >>> users = user_repo._get_all(session, is_active=True, role="user")
        
        Note:
            - Sadece eşitlik (==) kontrolü yapar
            - Tüm filtreler AND ile birleştirilir
            - Model'de olmayan alanlar için warning print edilir
            - None değerleri IS NULL'a otomatik çevrilir
            - Performanslı: Operatör kontrolü yok
        
        Comparison with _apply_filters():
            - _apply_simple_filters: Sadece eşitlik, hızlı, basit
            - _apply_filters: 12 operatör, search, karmaşık
        
        When to Use:
            - Basit eşitlik kontrolleri için (_get_all, _get_or_create vb.)
            - Performans kritik durumlarda
            - Karmaşık operatör gerekmediğinde
        """
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
            else:
                print(f"Attempted to filter by non-existent field '{key}' on {self.model_name}")
        return query

    def _apply_soft_delete_filter(self, query: Select, include_deleted: bool = False) -> Select:
        """
        Soft delete filtresini sorguya uygular.
        
        Bu yardımcı fonksiyon, soft delete destekleyen modeller için
        silinmiş kayıtları filtrelemek amacıyla kullanılır. Model'de
        'is_deleted' alanı varsa, bu alan üzerinden WHERE koşulu ekler.
        
        Args:
            query (Select): Filtre uygulanacak SQLAlchemy select query
            include_deleted (bool): Silinmiş kayıtları da dahil et mi?
                - False (varsayılan): Sadece is_deleted=False kayıtlar
                - True: Tüm kayıtlar (silinmiş + aktif)
        
        Returns:
            Select: Filtrelenmiş SQLAlchemy query
        
        Çalışma Mantığı:
            1. include_deleted=True ise → Query'yi olduğu gibi döndür (filtre yok)
            2. Model'de 'is_deleted' alanı var mı kontrol et
            3. Varsa: WHERE is_deleted = False ekle
            4. Yoksa: Query'yi olduğu gibi döndür (soft delete desteklemiyor)
        
        Examples:
            >>> # Normal kullanım: Sadece aktif kayıtlar
            >>> query = select(User)
            >>> query = self._apply_soft_delete_filter(query, include_deleted=False)
            >>> # WHERE is_deleted = False
            
            >>> # Silinmiş kayıtları da dahil et
            >>> query = select(User)
            >>> query = self._apply_soft_delete_filter(query, include_deleted=True)
            >>> # Filtre eklenmez, tüm kayıtlar gelir
            
            >>> # Model soft delete desteklemiyorsa
            >>> query = select(SomeModel)  # is_deleted alanı yok
            >>> query = self._apply_soft_delete_filter(query, include_deleted=False)
            >>> # Filtre eklenmez (hasattr check)
            
            >>> # _get_all metodunda kullanım
            >>> def _get_all(self, session, include_deleted=False, **filters):
            ...     query = select(self.model)
            ...     query = self._apply_soft_delete_filter(query, include_deleted)
            ...     query = self._apply_simple_filters(query, **filters)
            ...     return session.execute(query).scalars().all()
            >>> 
            >>> # Sadece aktif kullanıcılar
            >>> users = user_repo._get_all(session)  # include_deleted=False
            >>> 
            >>> # Tüm kullanıcılar (silinmiş dahil)
            >>> all_users = user_repo._get_all(session, include_deleted=True)
        
        Soft Delete Pattern:
            - Kayıtlar fiziksel olarak silinmez
            - is_deleted flag'i True yapılır
            - deleted_at timestamp set edilir
            - Normal sorgularda görünmezler (bu filtre sayesinde)
            - Audit trail ve geri yükleme için önemli
        
        Note:
            - Model'de 'is_deleted' alanı yoksa filtre uygulanmaz
            - hasattr() ile güvenli kontrol yapılır
            - include_deleted=True tüm kayıtları döndürür (filter yok)
            - Tutarlılık için tüm query metodlarında kullanılır
        
        Related Methods:
            - _soft_delete(): Kaydı soft delete yapar
            - _restore(): Soft delete edilmiş kaydı geri yükler
            - _get_by_id(include_deleted=True): Silinen kayıtlara erişim
        
        When to Use include_deleted=True:
            - Admin panellerinde silinmiş kayıtları göstermek için
            - Geri yükleme (restore) işlemlerinde
            - Audit ve reporting için
            - _restore() metodunda (silinen kayıtları bulmak için)
        """
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = query.where(getattr(self.model, 'is_deleted').is_(False))
        return query

    def _apply_ordering(self, query: Select, order_by: Optional[str] = None, order_desc: bool = False) -> Select:
        """
        Sorguya sıralama (ORDER BY) uygular.
        
        Bu yardımcı fonksiyon, SQLAlchemy query'sine ORDER BY koşulu ekler.
        Artan (ASC) veya azalan (DESC) sıralama yapabilir. Model'de olmayan
        alanlar için warning verir.
        
        Args:
            query (Select): Sıralama uygulanacak SQLAlchemy select query
            order_by (Optional[str]): Sıralama yapılacak alan adı
                - None ise: Sıralama yapılmaz (database default order)
                - String ise: O alana göre sıralama yapılır
            order_desc (bool): Azalan sıralama mı?
                - False (varsayılan): Artan sıralama (ASC)
                - True: Azalan sıralama (DESC)
        
        Returns:
            Select: Sıralanmış SQLAlchemy query
        
        Çalışma Mantığı:
            1. order_by None ise → Query'yi olduğu gibi döndür (sıralama yok)
            2. Model'de order_by alanı var mı kontrol et
            3. Varsa:
               a. order_desc=True ise → ORDER BY field DESC
               b. order_desc=False ise → ORDER BY field ASC
            4. Yoksa: Print warning ver ve query'yi olduğu gibi döndür
        
        Examples:
            >>> # Artan sıralama (ASC)
            >>> query = select(User)
            >>> query = self._apply_ordering(query, order_by="name", order_desc=False)
            >>> # ORDER BY name ASC
            
            >>> # Azalan sıralama (DESC)
            >>> query = select(User)
            >>> query = self._apply_ordering(query, order_by="created_at", order_desc=True)
            >>> # ORDER BY created_at DESC (en yeni önce)
            
            >>> # Sıralama yok
            >>> query = select(User)
            >>> query = self._apply_ordering(query, order_by=None)
            >>> # ORDER BY yok, database default order
            
            >>> # Geçersiz alan
            >>> query = select(User)
            >>> query = self._apply_ordering(query, order_by="non_existent_field")
            >>> # Warning: "Attempted to order by non-existent field..."
            >>> # Query değişmez
            
            >>> # _get_all metodunda kullanım
            >>> def _get_all(self, session, order_by=None, order_desc=False, **filters):
            ...     query = select(self.model)
            ...     query = self._apply_simple_filters(query, **filters)
            ...     query = self._apply_ordering(query, order_by, order_desc)
            ...     return session.execute(query).scalars().all()
            >>> 
            >>> # En yeni kullanıcılar önce
            >>> users = user_repo._get_all(
            ...     session,
            ...     order_by="created_at",
            ...     order_desc=True
            ... )
            >>> 
            >>> # İsme göre alfabetik
            >>> users = user_repo._get_all(
            ...     session,
            ...     order_by="name",
            ...     order_desc=False
            ... )
        
        Common Use Cases:
            - created_at DESC: En yeni kayıtlar önce
            - updated_at DESC: Son güncellenenler önce
            - name ASC: Alfabetik sıralama
            - age DESC: En yaşlıdan gence
            - price ASC: En ucuzdan pahalıya
            - priority DESC: Öncelik sıralaması
        
        Note:
            - order_by None ise hiçbir sıralama uygulanmaz
            - Model'de olmayan alanlar için warning print edilir (exception fırlatmaz)
            - ASC: ascending (küçükten büyüğe, A-Z, eskiden yeniye)
            - DESC: descending (büyükten küçüğe, Z-A, yeniden eskiye)
            - Database default order genellikle insertion order'dır
        
        Performance Note:
            - ORDER BY performansı etkileyebilir
            - Sıralanan alan üzerinde index olması önerilir
            - Büyük veri setlerinde LIMIT ile birlikte kullanın
        
        Related Methods:
            - _get_first(): order_by ile ilk kaydı alır
            - _get_last(): order_by'ı tersine çevirip son kaydı alır
            - _get_all(): Liste döndürür, sıralı
            - _paginate(): Sayfalama + sıralama
        """
        if order_by:
            if hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                print(f"Attempted to order by non-existent field '{order_by}' on {self.model_name}")
        return query

    # ============================================================================
    # CRUD OPERATIONS
    # ============================================================================

    @_handle_db_exceptions
    def _create(
        self,
        session: Session,
        *,
        created_by: Optional[str] = None,
        **kwargs: Any
    ) -> ModelType:
        """
        Yeni bir kayıt oluşturur.
        
        Veritabanına yeni bir kayıt ekler ve oluşturulan objeyi döndürür.
        Metod flush() kullanır, commit() yapmaz - transaction yönetimi 
        çağıran tarafa bırakılmıştır.
        
        Args:
            session (Session): Veritabanı oturumu
            created_by (Optional[str]): Kaydı oluşturan kullanıcının ID'si.
                Model'de created_by alanı varsa otomatik set edilir.
            **kwargs (Any): Yeni kayıt için alan değerleri (name="John", age=30 gibi)
        
        Returns:
            ModelType: Oluşturulan ve veritabanına eklenmiş model instance
        
        Raises:
            DatabaseValidationError: kwargs boş ise
            DatabaseValidationError: Zorunlu alanlar eksik ise
            DatabaseValidationError: Unique constraint ihlali varsa
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit kullanım
            >>> user = user_repo._create(
            ...     session,
            ...     email="user@example.com",
            ...     name="John Doe",
            ...     age=30
            ... )
            >>> print(user.id)  # Auto-generated ID
            
            >>> # Created_by ile
            >>> product = product_repo._create(
            ...     session,
            ...     name="Laptop",
            ...     price=999.99,
            ...     created_by="admin_user_id"
            ... )
            
            >>> # Transaction yönetimi
            >>> try:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     profile = profile_repo._create(session, user_id=user.id)
            ...     session.commit()  # İkisi de başarılı
            ... except Exception:
            ...     session.rollback()  # Hata varsa geri al
        
        Note:
            Bu metod flush() kullanır, commit() kullanmaz. Çağıran taraf 
            transaction'ı commit etmekten sorumludur. Bu sayede birden fazla
            işlem tek bir transaction içinde yapılabilir.
        """
        if not kwargs:
            raise DatabaseValidationError()
        
        if created_by and hasattr(self.model, 'created_by'):
            kwargs['created_by'] = created_by
        
        obj = cast(ModelType, self.model(**kwargs))
        session.add(obj)
        session.flush()
        return obj
    
    @_handle_db_exceptions
    def _get_by_id(
        self,
        session: Session,
        *,
        record_id: str,
        raise_not_found: bool = True,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        ID'ye göre tek bir kayıt getirir.
        
        Verilen ID'ye sahip kaydı veritabanından getirir. Kayıt bulunamazsa
        raise_not_found parametresine göre hata fırlatır veya None döner.
        Soft delete desteği ile silinmiş kayıtları filtreleyebilir.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Getirilecek kaydın ID'si
            raise_not_found (bool): Kayıt bulunamazsa hata fırlatılsın mı?
                True ise DatabaseValidationError fırlatır, False ise None döner.
                Varsayılan: True
            include_deleted (bool): Silinmiş (soft delete) kayıtları da dahil et.
                False ise is_deleted=True olan kayıtlar göz ardı edilir.
                Varsayılan: False
        
        Returns:
            Optional[ModelType]: Bulunan model instance veya None
                - raise_not_found=True ve kayıt yoksa: Exception fırlatır
                - raise_not_found=False ve kayıt yoksa: None döner
                - Kayıt varsa: Model instance döner
        
        Raises:
            DatabaseValidationError: Kayıt bulunamazsa (raise_not_found=True ise)
            DatabaseConnectionError: Veritabanı bağlantı sorunu varsa
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit kullanım - kayıt bulunmalı
            >>> user = user_repo._get_by_id(session, record_id="user123")
            >>> print(user.email)
            
            >>> # Hata fırlatmadan kontrol et
            >>> user = user_repo._get_by_id(
            ...     session, 
            ...     record_id="maybe_exists",
            ...     raise_not_found=False
            ... )
            >>> if user:
            ...     print(f"Found: {user.name}")
            ... else:
            ...     print("Not found")
            
            >>> # Silinmiş kayıtları da getir
            >>> deleted_user = user_repo._get_by_id(
            ...     session,
            ...     record_id="deleted_user_id",
            ...     include_deleted=True
            ... )
            >>> if deleted_user and deleted_user.is_deleted:
            ...     print("Bu kullanıcı silinmiş")
            
            >>> # Restore işlemi için
            >>> user = user_repo._get_by_id(
            ...     session,
            ...     record_id="user_to_restore",
            ...     include_deleted=True  # Silinmiş kaydı bul
            ... )
            >>> if user:
            ...     user_repo._restore(session, record_id=user.id)
        
        Note:
            - session.get() kullanır, bu yüzden performanslıdır (primary key lookup)
            - Soft delete kontrolü model'de is_deleted alanı varsa otomatik yapılır
            - include_deleted=False iken silinmiş kayıt "bulunamadı" gibi davranır
        """
        result = session.get(self.model, record_id)

        # Soft delete check
        if result and not include_deleted and hasattr(self.model, 'is_deleted'):
            if getattr(result, 'is_deleted', False):
                if raise_not_found:
                    self._raise_not_found_error(record_id)
                return None

        if result is None and raise_not_found:
            self._raise_not_found_error(record_id)

        return result
    
    @_handle_db_exceptions
    def _update(
        self, 
        session: Session,
        *,
        record_id: str,
        updated_by: Optional[str] = None,
        **kwargs: Any
    ) -> ModelType:
        """
        Mevcut bir kaydı günceller.
        
        Verilen ID'ye sahip kaydı bulur ve belirtilen alanları günceller.
        Güncellenen objeyi döndürür. Kayıt bulunamazsa hata fırlatır.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Güncellenecek kaydın ID'si
            updated_by (Optional[str]): Kaydı güncelleyen kullanıcının ID'si.
                Model'de updated_by alanı varsa otomatik set edilir.
            **kwargs (Any): Güncellenecek alan ve değerleri (name="Jane", age=31 gibi)
        
        Returns:
            ModelType: Güncellenmiş model instance
        
        Raises:
            DatabaseValidationError: kwargs boş ise
            DatabaseValidationError: Kayıt bulunamazsa
            DatabaseConnectionError: Veritabanı bağlantı sorunu
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit güncelleme
            >>> user = user_repo._update(
            ...     session,
            ...     record_id="user123",
            ...     name="Jane Doe",
            ...     age=31
            ... )
            
            >>> # updated_by ile
            >>> product = product_repo._update(
            ...     session,
            ...     record_id="prod456",
            ...     price=899.99,
            ...     updated_by="admin_id"
            ... )
            
            >>> # Kısmi güncelleme
            >>> user = user_repo._update(
            ...     session,
            ...     record_id="user789",
            ...     is_active=False  # Sadece bir alan
            ... )
        
        Note:
            - Sadece silinmemiş (is_deleted=False) kayıtları günceller
            - Var olmayan alanlar göz ardı edilir (print uyarısı verir)
            - flush() kullanır, commit() kullanmaz
        """
        
        if not kwargs:
            raise DatabaseValidationError()
        
        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True)

        if updated_by and hasattr(self.model, 'updated_by'):
            kwargs['updated_by'] = updated_by

        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                print(f"Attempted to update non-existent field '{key}' on {self.model_name}")

        session.add(obj)
        session.flush()
        return obj
    
    @_handle_db_exceptions
    def _delete(
        self,
        session: Session,
        *,
        record_id: str,
    ) -> ModelType:
        """
        Kaydı kalıcı olarak siler (hard delete).
        
        Verilen ID'ye sahip kaydı veritabanından tamamen siler. Bu işlem geri alınamaz.
        Soft delete yerine kullanılmalıdır sadece gerçekten silinmesi gereken kayıtlar için.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Silinecek kaydın ID'si
        
        Returns:
            ModelType: Silinen model instance (silme öncesi hali)
        
        Raises:
            DatabaseValidationError: Kayıt bulunamazsa
            DatabaseConnectionError: Veritabanı bağlantı sorunu
            DatabaseError: Foreign key constraint ihlali gibi diğer hatalar
        
        Examples:
            >>> # Kalıcı silme
            >>> deleted_user = user_repo._delete(
            ...     session,
            ...     record_id="user123"
            ... )
            >>> print(f"Silinen: {deleted_user.email}")
            
            >>> # Transaction ile
            >>> try:
            ...     user = user_repo._delete(session, record_id="user456")
            ...     session.commit()
            ... except Exception:
            ...     session.rollback()
        
        Warning:
            Bu işlem GERİ ALINAMAZ! Soft delete için _soft_delete() kullanın.
        
        Note:
            - Sadece silinmemiş kayıtları siler
            - Foreign key ilişkileri varsa hata verebilir
            - Audit log tutulması gereken durumlarda soft delete tercih edilmeli
        """

        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True)

        session.delete(obj)
        session.flush()

        return obj

    @_handle_db_exceptions
    def _soft_delete(
        self,
        session: Session,
        *,
        record_id: str,
        deleted_by: Optional[str] = None,
    ) -> ModelType:
        """
        Kaydı geçici olarak siler (soft delete).
        
        Kaydı fiziksel olarak silmek yerine is_deleted flag'ini True yapar ve
        deleted_at timestamp'ini set eder. Kayıt veritabanında kalır ama
        normal sorgularda görünmez. İleride restore edilebilir.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Soft delete yapılacak kaydın ID'si
            deleted_by (Optional[str]): Kaydı silen kullanıcının ID'si.
                Model'de deleted_by alanı varsa otomatik set edilir.
        
        Returns:
            ModelType: Soft delete edilmiş model instance
        
        Raises:
            DatabaseValidationError: Model soft delete desteklemiyorsa
                (is_deleted ve deleted_at alanları yoksa)
            DatabaseValidationError: Kayıt bulunamazsa veya zaten silinmişse
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit soft delete
            >>> user = user_repo._soft_delete(
            ...     session,
            ...     record_id="user123"
            ... )
            >>> print(user.is_deleted)  # True
            >>> print(user.deleted_at)  # datetime.now()
            
            >>> # deleted_by ile
            >>> product = product_repo._soft_delete(
            ...     session,
            ...     record_id="prod456",
            ...     deleted_by="admin_id"
            ... )
            
            >>> # Soft delete ve restore
            >>> user = user_repo._soft_delete(session, record_id="user789")
            >>> session.commit()
            >>> # İleride geri yükle
            >>> user = user_repo._restore(session, record_id="user789")
        
        Note:
            - Model'de is_deleted, deleted_at alanları olmalı
            - Zaten silinmiş kayıtları tekrar silemez
            - Audit trail için ideal (kim, ne zaman sildi bilgisi saklanır)
            - _restore() ile geri yüklenebilir
        """
        # Get non-deleted record only
        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True, include_deleted=False)

        if not (hasattr(self.model, 'is_deleted') and hasattr(self.model, 'deleted_at')):
            raise DatabaseValidationError()

        setattr(obj, 'is_deleted', True)
        setattr(obj, 'deleted_at', datetime.now(timezone.utc))

        if deleted_by and hasattr(self.model, 'deleted_by'):
            setattr(obj, 'deleted_by', deleted_by)

        session.add(obj)
        session.flush()

        return obj

    @_handle_db_exceptions
    def _restore(
        self,
        session: Session,
        *,
        record_id: str,
        restored_by: Optional[str] = None,
    ) -> ModelType:
        """
        Soft delete edilmiş bir kaydı geri yükler.
        
        Daha önce soft delete edilmiş (_soft_delete) bir kaydı aktif hale getirir.
        is_deleted flag'ini False yapar ve ilgili alanları temizler.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Geri yüklenecek kaydın ID'si
            restored_by (Optional[str]): Kaydı geri yükleyen kullanıcının ID'si.
                Model'de restored_by alanı varsa otomatik set edilir.
        
        Returns:
            ModelType: Geri yüklenmiş model instance
        
        Raises:
            DatabaseValidationError: Model soft delete desteklemiyorsa
            DatabaseValidationError: Kayıt bulunamazsa
            DatabaseValidationError: Kayıt zaten aktifse (silinmemişse)
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit restore
            >>> user = user_repo._restore(
            ...     session,
            ...     record_id="user123"
            ... )
            >>> print(user.is_deleted)  # False
            >>> print(user.deleted_at)  # None
            
            >>> # restored_by ile
            >>> product = product_repo._restore(
            ...     session,
            ...     record_id="prod456",
            ...     restored_by="admin_id"
            ... )
            
            >>> # Soft delete ve restore döngüsü
            >>> user = user_repo._soft_delete(session, record_id="user789")
            >>> session.commit()
            >>> # Kullanıcı fikir değiştirdi, geri yükle
            >>> user = user_repo._restore(session, record_id="user789")
            >>> print(user.is_deleted)  # False
        
        Note:
            - Sadece silinmiş (is_deleted=True) kayıtları geri yükleyebilir
            - include_deleted=True ile kayıt bulunur
            - Audit trail için restored_by alanı önerilir
        """
        # Get the record including deleted ones
        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True, include_deleted=True)

        if not (hasattr(self.model, 'is_deleted') and hasattr(self.model, 'deleted_at')):
            raise DatabaseValidationError()

        # Safe attribute access
        if not getattr(obj, 'is_deleted', False):
            raise DatabaseValidationError()

        setattr(obj, 'is_deleted', False)
        setattr(obj, 'deleted_at', None)

        if hasattr(self.model, 'deleted_by'):
            setattr(obj, 'deleted_by', None)

        if restored_by and hasattr(self.model, 'restored_by'):
            setattr(obj, 'restored_by', restored_by)
            setattr(obj, 'restored_at', datetime.now(timezone.utc))

        session.add(obj)
        session.flush()

        return obj

    @_handle_db_exceptions
    def _exists(
        self,
        session: Session,
        *,
        record_id: str,
        include_deleted: bool = False
    ) -> bool:
        """
        Check if a record exists by its ID.
        
        Args:
            session: Database session
            record_id: ID of the record to check
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            True if record exists, False otherwise
        """
        # Build exists query
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            query = exists().where(
                self.model.id == record_id,
                getattr(self.model, 'is_deleted').is_(False)
            )
        else:
            query = exists().where(self.model.id == record_id)
        
        return session.query(query).scalar()

    @_handle_db_exceptions
    def _count(
        self,
        session: Session,
        *,
        include_deleted: bool = False,
        filter_params: Optional[FilterParams] = None,
        **filters: Any
    ) -> int:
        """
        Count records with filters.
        
        Args:
            session: Database session
            include_deleted: Whether to include soft-deleted records
            filter_params: Advanced filter parameters with operators
            **filters: Simple equality filters (field=value)
            
        Returns:
            Count of matching records
            
        Example:
            # Simple count
            total = repo._count(session)
            
            # Count with simple filters
            active_users = repo._count(session, is_active=True)
            
            # Count with advanced filters
            filter_params = FilterParams()
            filter_params.add_filter("age", 18, "gte")
            filter_params.add_filter("age", 65, "lte")
            adults = repo._count(session, filter_params=filter_params)
        """
        query = select(func.count(self.model.id))

        # Apply soft delete filter
        query = self._apply_soft_delete_filter(query, include_deleted)
        
        # Apply advanced filters if provided
        if filter_params:
            query = self._apply_filters(query, filter_params)

        # Apply simple filters
        query = self._apply_simple_filters(query, **filters)

        result = session.execute(query).scalar()
        return result or 0

    @_handle_db_exceptions
    def _get_all(
        self,
        session: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        **filters: Any
    ) -> List[ModelType]:
        """
        Tüm kayıtları basit filtrelerle getirir.
        
        Veritabanından kayıtları basit eşitlik filtreleriyle getirir. Pagination
        (sayfalama), sıralama ve soft delete kontrolü destekler.
        
        Args:
            session (Session): Veritabanı oturumu
            skip (int): Atlanacak kayıt sayısı (offset). Varsayılan: 0
            limit (int): Maksimum getirilecek kayıt sayısı. Varsayılan: 100
            order_by (Optional[str]): Sıralama için alan adı
            order_desc (bool): Azalan sıralama mı? Varsayılan: False (artan)
            include_deleted (bool): Silinmiş kayıtları da dahil et. Varsayılan: False
            **filters (Any): Basit eşitlik filtreleri (is_active=True, role="admin" gibi)
            
        Returns:
            List[ModelType]: Model instance listesi (boş liste dönebilir)
        
        Raises:
            DatabaseConnectionError: Veritabanı bağlantı sorunu
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # İlk 10 kullanıcı
            >>> users = user_repo._get_all(session, limit=10)
            
            >>> # Aktif kullanıcılar, yaşa göre sıralı
            >>> active_users = user_repo._get_all(
            ...     session,
            ...     is_active=True,
            ...     order_by="age",
            ...     order_desc=True,
            ...     limit=50
            ... )
            
            >>> # Pagination için
            >>> page = 3
            >>> page_size = 20
            >>> users = user_repo._get_all(
            ...     session,
            ...     skip=(page - 1) * page_size,
            ...     limit=page_size
            ... )
            
            >>> # Silinmiş kayıtları da getir
            >>> all_users = user_repo._get_all(
            ...     session,
            ...     include_deleted=True
            ... )
        
        Note:
            - Basit eşitlik filtreleri (field=value) kullanır
            - Karmaşık filtreler için _filter() kullanın
            - Pagination için _paginate() daha kullanışlıdır
        """
        query = select(self.model)
        
        # Apply soft delete filter
        query = self._apply_soft_delete_filter(query, include_deleted)

        # Apply simple filters
        query = self._apply_simple_filters(query, **filters)

        # Apply ordering
        query = self._apply_ordering(query, order_by, order_desc)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        results = session.execute(query).scalars().all()
        return list(results)

    @_handle_db_exceptions
    def _filter(
        self,
        session: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        filter_params: Optional[FilterParams] = None,
    ) -> List[ModelType]:
        """
        Gelişmiş FilterParams ile kayıtları getirir.
        
        FilterParams kullanarak karmaşık sorgular yapabilirsiniz (>, <, LIKE, IN vb.).
        Basit eşitlik için _get_all() daha uygun olabilir.
        
        Args:
            session (Session): Veritabanı oturumu
            skip (int): Atlanacak kayıt sayısı. Varsayılan: 0
            limit (int): Maksimum kayıt sayısı. Varsayılan: 100
            order_by (Optional[str]): Sıralama alanı
            order_desc (bool): Azalan sıralama. Varsayılan: False
            include_deleted (bool): Silinmiş kayıtlar. Varsayılan: False
            filter_params (Optional[FilterParams]): Gelişmiş filtre parametreleri
            
        Returns:
            List[ModelType]: Filtrelenmiş model listesi
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # Yaşı 18'den büyük kullanıcılar
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gt")
            >>> adults = user_repo._filter(session, filter_params=filter_params)
            
            >>> # Yaş aralığı: 18-65
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gte")
            >>> filter_params.add_filter("age", 65, "lte")
            >>> users = user_repo._filter(session, filter_params=filter_params)
            
            >>> # Email'i "gmail" içerenler
            >>> filter_params = FilterParams()
            >>> filter_params.add_like_filter("email", "%gmail%", case_sensitive=False)
            >>> gmail_users = user_repo._filter(session, filter_params=filter_params)
            
            >>> # Arama (search)
            >>> filter_params = FilterParams()
            >>> filter_params.search = "john"
            >>> filter_params.search_fields = ["name", "email"]
            >>> results = user_repo._filter(session, filter_params=filter_params)
        
        Note:
            - Operatörler: eq, ne, gt, gte, lt, lte, in, like, ilike, is_null, is_not_null
            - Search ile birden fazla alanda arama yapabilir
        """
        query = select(self.model)

        # Apply soft delete filter
        query = self._apply_soft_delete_filter(query, include_deleted)

        # Apply advanced filters
        query = self._apply_filters(query, filter_params)
        
        # Apply ordering
        query = self._apply_ordering(query, order_by, order_desc)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        results = session.execute(query).scalars().all()
        return list(results)

    @_handle_db_exceptions
    def _get_first(
        self,
        session: Session,
        *,
        filter_params: Optional[FilterParams] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        İlk kaydı getirir (gelişmiş filtrelerle).
        
        FilterParams ile karmaşık filtreler + sıralama ile ilk kaydı döndürür.
        LIMIT 1 kullanır, kayıt yoksa None döner.
        
        Args:
            session (Session): Veritabanı oturumu
            filter_params (Optional[FilterParams]): Gelişmiş filtre parametreleri
            order_by (Optional[str]): Sıralama alanı
            order_desc (bool): Azalan sıralama. Varsayılan: False
            include_deleted (bool): Silinmiş kayıtlar. Varsayılan: False
        
        Returns:
            Optional[ModelType]: İlk kayıt veya None
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # En genç yetişkin (age > 18)
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gt")
            >>> youngest_adult = user_repo._get_first(
            ...     session,
            ...     filter_params=filter_params,
            ...     order_by="age",
            ...     order_desc=False
            ... )
            
            >>> # En yeni aktif kullanıcı
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("is_active", True, "eq")
            >>> newest = user_repo._get_first(
            ...     session,
            ...     filter_params=filter_params,
            ...     order_by="created_at",
            ...     order_desc=True
            ... )
        
        Note:
            - Karmaşık filtreler için kullanılır
            - _filter() metodunu LIMIT 1 ile çağırır
        """

        results = self._filter(
            session=session,
            filter_params=filter_params or FilterParams(),
            skip=0,
            limit=1,
            order_by=order_by,
            order_desc=order_desc,
            include_deleted=include_deleted
        )
        return results[0] if results else None

    @_handle_db_exceptions
    def _get_last(
        self,
        session: Session,
        *,
        filter_params: Optional[FilterParams] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Son kaydı getirir (gelişmiş filtrelerle).
        
        FilterParams ile karmaşık filtreler + sıralama ile son kaydı döndürür.
        İçeride sıralamayı tersine çevirerek LIMIT 1 ile optimize eder.
        
        Args:
            session (Session): Veritabanı oturumu
            filter_params (Optional[FilterParams]): Gelişmiş filtre parametreleri
            order_by (Optional[str]): Sıralama alanı
            order_desc (bool): Doğal sıralama azalan mı? Varsayılan: False
            include_deleted (bool): Silinmiş kayıtlar. Varsayılan: False
            
        Returns:
            Optional[ModelType]: Son kayıt veya None
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # En yaşlı yetişkin (age > 18)
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gt")
            >>> oldest_adult = user_repo._get_last(
            ...     session,
            ...     filter_params=filter_params,
            ...     order_by="age",
            ...     order_desc=False  # Artan sırada son = en büyük
            ... )
            
            >>> # En eski kullanıcı
            >>> newest = user_repo._get_last(
            ...     session,
            ...     order_by="created_at",
            ...     order_desc=True  # Azalan sırada son = en eski
            ... )
            
        Note:
            - Sıralamayı tersine çevirerek (not order_desc) optimize eder
            - _filter() metodunu LIMIT 1 ile çağırır
        """
        results = self._filter(
            session=session,
            filter_params=filter_params or FilterParams(),
            skip=0,
            limit=1,
            order_by=order_by,
            order_desc=not order_desc,  # Reverse order to get last efficiently
            include_deleted=include_deleted
        )
        return results[0] if results else None

    @_handle_db_exceptions
    def _paginate(
        self,
        session: Session,
        *,
        pagination_params: PaginationParams,
        filter_params: Optional[FilterParams] = None,
        **simple_filters: Any
    ) -> PaginatedResponse[ModelType]:
        """
        Kayıtları sayfalandırır (pagination) - gelişmiş filtreleme ile.
        
        Tam özellikli sayfalama: sayfa numarası, sayfa boyutu, sıralama,
        gelişmiş filtreler ve basit filtreler. PaginatedResponse döndürür.
        
        Args:
            session (Session): Veritabanı oturumu
            pagination_params (PaginationParams): Sayfalama parametreleri
                - page: Sayfa numarası (1'den başlar)
                - page_size: Sayfa başına kayıt sayısı
                - order_by: Sıralama alanı
                - order_desc: Azalan sıralama
                - include_deleted: Silinmiş kayıtları dahil et
            filter_params (Optional[FilterParams]): Gelişmiş filtre parametreleri
                (>, <, LIKE, IN vb. operatörlerle)
            **simple_filters (Any): Basit eşitlik filtreleri (is_active=True gibi)
        
        Returns:
            PaginatedResponse[ModelType]: Sayfalanmış sonuç
                - items: Mevcut sayfadaki kayıtlar
                - pagination: Metadata (total, pages, current_page vb.)
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # Basit sayfalama
            >>> pagination_params = PaginationParams(page=1, page_size=20)
            >>> result = user_repo._paginate(session, pagination_params=pagination_params)
            >>> print(f"Toplam: {result.pagination.total_items}")
            >>> print(f"Sayfa: {result.pagination.current_page}/{result.pagination.total_pages}")
            >>> for user in result.items:
            ...     print(user.name)
            
            >>> # Filtreleme + Sayfalama
            >>> filter_params = FilterParams()
            >>> filter_params.add_filter("age", 18, "gte")
            >>> pagination_params = PaginationParams(
            ...     page=2,
            ...     page_size=10,
            ...     order_by="name"
            ... )
            >>> result = user_repo._paginate(
            ...     session,
            ...     pagination_params=pagination_params,
            ...     filter_params=filter_params,
            ...     is_active=True  # Basit filtre
            ... )
            
            >>> # Arama + Sayfalama
            >>> filter_params = FilterParams()
            >>> filter_params.search = "john"
            >>> filter_params.search_fields = ["name", "email"]
            >>> pagination_params = PaginationParams(page=1, page_size=50)
            >>> result = user_repo._paginate(
            ...     session,
            ...     pagination_params=pagination_params,
            ...     filter_params=filter_params
            ... )
        
        Note:
            - Hem gelişmiş hem basit filtreleri destekler
            - Performanslı count query kullanır
            - Toplam sayfa sayısını otomatik hesaplar
            - Frontend pagination için ideal
        """
        query = select(self.model)

        # Apply soft delete filter from pagination_params
        query = self._apply_soft_delete_filter(query, pagination_params.include_deleted)

        # Apply advanced filters if provided
        if filter_params:
            query = self._apply_filters(query, filter_params)

        # Apply simple filters
        query = self._apply_simple_filters(query, **simple_filters)

        # Count total items before pagination (count primary key for better performance)
        count_query = select(func.count(self.model.id))
        count_query = self._apply_soft_delete_filter(count_query, pagination_params.include_deleted)
        if filter_params:
            count_query = self._apply_filters(count_query, filter_params)
        count_query = self._apply_simple_filters(count_query, **simple_filters)
        total_items = session.execute(count_query).scalar() or 0

        # Apply ordering from pagination_params
        query = self._apply_ordering(query, pagination_params.order_by, pagination_params.order_desc)

        # Apply pagination
        query = query.offset(pagination_params.skip).limit(pagination_params.limit)

        items = list(session.execute(query).scalars().all())
        
        metadata = PaginationMetadata.from_params(pagination_params, total_items)
        
        return PaginatedResponse(items=items, metadata=metadata)

    @_handle_db_exceptions
    def _get_by_ids(
        self,
        session: Session,
        *,
        record_ids: List[str],
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Birden fazla ID ile kayıtları tek sorguda getirir (N+1 önleyici).
        
        N+1 query problemini önlemek için birden fazla ID'yi IN operatörü ile
        tek sorguda getirir. Loop içinde tek tek getirmek yerine bu metodu kullanın.
        
        Args:
            session (Session): Veritabanı oturumu
            record_ids (List[str]): Getirilecek kayıtların ID listesi
            include_deleted (bool): Silinmiş kayıtlar. Varsayılan: False
        
        Returns:
            List[ModelType]: Bulunan kayıtların listesi (boş liste dönebilir)
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # Birden fazla kullanıcı getir
            >>> user_ids = ["user1", "user2", "user3"]
            >>> users = user_repo._get_by_ids(session, record_ids=user_ids)
            >>> print(f"{len(users)} kullanıcı bulundu")
            
            >>> # N+1 problemi - YANLIŞ ❌
            >>> for user_id in user_ids:
            ...     user = user_repo._get_by_id(session, record_id=user_id)
            ...     # Her döngü için 1 query = N+1 problem!
            
            >>> # Doğru yaklaşım - TEK QUERY ✅
            >>> users = user_repo._get_by_ids(session, record_ids=user_ids)
            >>> for user in users:
            ...     # Tek query ile tüm kayıtlar geldi
            
            >>> # Silinmiş kayıtları da getir
            >>> all_users = user_repo._get_by_ids(
            ...     session,
            ...     record_ids=user_ids,
            ...     include_deleted=True
            ... )
        
        Note:
            - Boş liste verilirse boş liste döner (query atılmaz)
            - Bulunamayan ID'ler için None dönmez, sadece bulunanlar gelir
            - Performans için IN operatörü kullanır
            - N+1 problemini önlemek için kritik metod
        """
        if not record_ids:
            return []

        query = select(self.model).where(self.model.id.in_(record_ids))
        
        # Apply soft delete filter
        query = self._apply_soft_delete_filter(query, include_deleted)
        
        results = session.execute(query).scalars().all()
        return list(results)

    @_handle_db_exceptions
    def _get_or_create(
        self,
        session: Session,
        *,
        defaults: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        **filters: Any
    ) -> Tuple[ModelType, bool]:
        """
        Varsa getirir, yoksa oluşturur (get_or_create pattern).
        
        Çok yaygın bir pattern: Kayıt varsa onu döndür, yoksa yeni oluştur.
        Race condition'ları (eşzamanlı oluşturma) güvenli şekilde handle eder.
        
        Args:
            session (Session): Veritabanı oturumu
            defaults (Optional[Dict[str, Any]]): Oluşturma sırasında eklenecek ekstra alanlar
                (lookup'ta kullanılmaz, sadece oluşturma sırasında eklenir)
            created_by (Optional[str]): Kaydı oluşturan kullanıcının ID'si
            **filters (Any): Arama ve oluşturma için kullanılacak alanlar
                (email="test@example.com", username="john" gibi)
        
        Returns:
            Tuple[ModelType, bool]: (instance, created)
                - instance: Bulunan veya oluşturulan kayıt
                - created: True ise yeni oluşturuldu, False ise mevcut kayıt bulundu
        
        Raises:
            DatabaseValidationError: filters boşsa
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit get_or_create
            >>> user, created = user_repo._get_or_create(
            ...     session,
            ...     email="user@example.com",
            ...     defaults={"name": "John Doe", "age": 30},
            ...     created_by="admin"
            ... )
            >>> if created:
            ...     print(f"Yeni kullanıcı oluşturuldu: {user.email}")
            ... else:
            ...     print(f"Mevcut kullanıcı bulundu: {user.email}")
            
            >>> # defaults olmadan
            >>> tag, created = tag_repo._get_or_create(
            ...     session,
            ...     name="Python",
            ...     slug="python"  # Bu alan hem lookup hem create için kullanılır
            ... )
            
            >>> # Race condition güvenli
            >>> # İki thread aynı anda çalışsa bile sadece biri oluşturur
            >>> product, created = product_repo._get_or_create(
            ...     session,
            ...     sku="PROD-12345",
            ...     defaults={
            ...         "name": "Widget",
            ...         "price": 99.99
            ...     }
            ... )
        
        Note:
            - filters: Hem arama hem oluşturma için kullanılır
            - defaults: Sadece oluşturma için kullanılır (lookup'ta değil)
            - Race condition: IntegrityError yakalanır, tekrar arama yapılır
            - Sadece silinmemiş kayıtları arar (include_deleted=False)
        
        Warning:
            filters mutlaka unique constraint olan alanlar olmalı,
            yoksa her seferinde yeni kayıt oluşturur!
        """
        if not filters:
            raise DatabaseValidationError()

        # Try to get existing record
        query = select(self.model)
        query = self._apply_simple_filters(query, **filters)
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        
        result = session.execute(query).scalar_one_or_none()
        
        if result:
            return result, False
        
        # Record doesn't exist, create it
        try:
            create_data = {**filters}
            if defaults:
                create_data.update(defaults)
            
            obj = self._create(session, created_by=created_by, **create_data)
            return obj, True
            
        except DatabaseValidationError as e:
            # Check if the original error was IntegrityError (race condition)
            # The decorator converts IntegrityError to DatabaseValidationError
            if e.__cause__ and isinstance(e.__cause__, IntegrityError):
                # Race condition: another process created it between our check and insert
                # Try to get it again
                query = select(self.model)
                query = self._apply_simple_filters(query, **filters)
                query = self._apply_soft_delete_filter(query, include_deleted=False)
                
                result = session.execute(query).scalar_one_or_none()
                if result:
                    return result, False
            
            # Not a race condition or still not found, re-raise
            raise

    @_handle_db_exceptions
    def _upsert(
        self,
        session: Session,
        *,
        unique_fields: List[str],
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        **data: Any
    ) -> Tuple[ModelType, bool]:
        """
        Varsa günceller, yoksa oluşturur (upsert operasyonu).
        
        Unique alanlarına göre kayıt arar. Varsa günceller, yoksa yeni oluşturur.
        Race condition'ları güvenli şekilde handle eder. SQL'deki UPSERT/MERGE ile benzer.
        
        Args:
            session (Session): Veritabanı oturumu
            unique_fields (List[str]): Benzersizlik kontrolü için alan adları
                (ör: ["email"], ["workspace_id", "name"])
            created_by (Optional[str]): Kaydı oluşturan kullanıcı (oluşturma durumunda)
            updated_by (Optional[str]): Kaydı güncelleyen kullanıcı (güncelleme durumunda)
            **data (Any): Tüm alan değerleri (unique_fields dahil)
        
        Returns:
            Tuple[ModelType, bool]: (instance, created)
                - instance: Güncellenen veya oluşturulan kayıt
                - created: True ise yeni oluşturuldu, False ise güncellendi
        
        Raises:
            DatabaseValidationError: unique_fields boşsa
            DatabaseValidationError: data boşsa
            DatabaseValidationError: unique_fields data'da yoksa
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Basit upsert (email ile)
            >>> user, created = user_repo._upsert(
            ...     session,
            ...     unique_fields=["email"],
            ...     email="user@example.com",
            ...     name="John Doe",
            ...     age=30,
            ...     created_by="admin"
            ... )
            >>> if created:
            ...     print(f"Yeni kullanıcı: {user.name}")
            ... else:
            ...     print(f"Güncellendi: {user.name}")
            
            >>> # Çoklu unique field (composite key)
            >>> member, created = member_repo._upsert(
            ...     session,
            ...     unique_fields=["workspace_id", "user_id"],
            ...     workspace_id="ws123",
            ...     user_id="user456",
            ...     role="admin",
            ...     updated_by="system"
            ... )
            
            >>> # Sync operasyonu için ideal
            >>> # External API'den gelen data'yı senkronize et
            >>> for api_user in external_api_users:
            ...     user, created = user_repo._upsert(
            ...         session,
            ...         unique_fields=["external_id"],
            ...         external_id=api_user["id"],
            ...         name=api_user["name"],
            ...         email=api_user["email"],
            ...         updated_by="sync_job"
            ...     )
        
        Note:
            - unique_fields: Arama için kullanılır, güncellenmez
            - data'nın geri kalanı: Güncelleme veya oluşturma için kullanılır
            - Race condition: IntegrityError yakalanır, tekrar arama yapılır
            - Eğer mevcut kayıtta unique_fields dışında değişiklik yoksa flush atlanır
        
        Warning:
            unique_fields mutlaka database'de unique constraint olmalı,
            yoksa her seferinde yeni kayıt oluşturur!
        """
        if not unique_fields:
            raise DatabaseValidationError()
        
        if not data:
            raise DatabaseValidationError()
        
        # Validate that all unique fields are in data
        missing_fields = [field for field in unique_fields if field not in data]
        if missing_fields:
            raise DatabaseValidationError()
        
        # Build filter for unique fields
        filters = {field: data[field] for field in unique_fields}
        
        # Try to find existing record
        query = select(self.model)
        query = self._apply_simple_filters(query, **filters)
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        
        existing = session.execute(query).scalar_one_or_none()
        
        if existing:
            # Update existing record
            update_data = {k: v for k, v in data.items() if k not in unique_fields}
            
            if not update_data:
                # No fields to update, return existing
                return existing, False
            
            for key, value in update_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            if updated_by and hasattr(self.model, 'updated_by'):
                setattr(existing, 'updated_by', updated_by)
            
            session.add(existing)
            session.flush()
            return existing, False
        
        # Create new record
        try:
            obj = self._create(session, created_by=created_by, **data)
            return obj, True
        except DatabaseValidationError as e:
            # Check if the original error was IntegrityError (race condition)
            if e.__cause__ and isinstance(e.__cause__, IntegrityError):
                # Race condition: another process created it, try to get and update it
                query = select(self.model)
                query = self._apply_simple_filters(query, **filters)
                query = self._apply_soft_delete_filter(query, include_deleted=False)
                
                existing = session.execute(query).scalar_one_or_none()
                if existing:
                    # Update the existing record
                    update_data = {k: v for k, v in data.items() if k not in unique_fields}
                    if update_data:
                        for key, value in update_data.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        
                        if updated_by and hasattr(self.model, 'updated_by'):
                            setattr(existing, 'updated_by', updated_by)
                        
                        session.add(existing)
                        session.flush()
                    
                    return existing, False
            
            # Not a race condition or still not found, re-raise
            raise

    @_handle_db_exceptions
    def _refresh(
        self,
        session: Session,
        *,
        obj: ModelType
    ) -> ModelType:
        """
        Objeyi veritabanından yeniden yükler (refresh).
        
        Objenin tüm attributelerini veritabanından tekrar okur. Local değişiklikleri iptal eder.
        Başka process'lerin yaptığı güncellemeleri görmek için kullanılır.
        
        Args:
            session (Session): Veritabanı oturumu
            obj (ModelType): Yenilenecek model instance
        
        Returns:
            ModelType: Yeniden yüklenmiş model instance (aynı obje referansı)
        
        Raises:
            DatabaseError: Veritabanı hataları
        
        Examples:
            >>> # Başka bir işlemin güncelleme yaptığı durum
            >>> user = user_repo._get_by_id(session, record_id="user123")
            >>> print(user.login_count)  # 10
            >>> # Başka bir process login_count'u artırdı
            >>> user = user_repo._refresh(session, obj=user)
            >>> print(user.login_count)  # 11 (güncel değer)
            
            >>> # Race condition sonrası güncel veriyi al
            >>> product = product_repo._create(session, name="Widget", stock=100)
            >>> # Başka bir thread stock'u değiştirdi
            >>> product = product_repo._refresh(session, obj=product)
            >>> print(product.stock)  # Güncel değer
            
            >>> # Session'daki pending değişiklikleri iptal etme
            >>> user.name = "John"  # Local değişiklik
            >>> user = user_repo._refresh(session, obj=user)
            >>> print(user.name)  # Veritabanındaki eski değer (değişiklik iptal)
        
        Note:
            - SQLAlchemy session.refresh() kullanır
            - Objenin tüm attributelerini yeniden yükler
            - Local (uncommitted) değişiklikleri iptal eder
            - İlişkili objeler (relationships) varsayılan olarak yenilenmez
            - Obje session'a attached olmalı
        
        Warning:
            Local değişiklikler kaybolur! Flush/commit yapmadan kullanmayın.
        """
        session.refresh(obj)
        return obj

    @_handle_db_exceptions
    def _increment(
        self,
        session: Session,
        *,
        record_id: str,
        field: str,
        amount: Union[int, float] = 1,
        updated_by: Optional[str] = None
    ) -> ModelType:
        """
        Sayısal bir alanı belirtilen miktarda artırır (atomik).
        
        Sayısal bir alanı atomik olarak artırır. Counter'lar için idealdir:
        view_count, like_count, stock_quantity, login_count vb.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Güncellenecek kaydın ID'si
            field (str): Artırılacak sayısal alanın adı
            amount (Union[int, float]): Artırılacak miktar. Varsayılan: 1
            updated_by (Optional[str]): İşlemi yapan kullanıcının ID'si
        
        Returns:
            ModelType: Güncellenmiş model instance
        
        Raises:
            DatabaseValidationError: Kayıt bulunamazsa
            DatabaseValidationError: Alan mevcut değilse
            DatabaseValidationError: Alan sayısal değilse
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # View count artırma
            >>> post = post_repo._increment(
            ...     session,
            ...     record_id="post123",
            ...     field="view_count"
            ... )
            >>> print(f"Views: {post.view_count}")
            
            >>> # Like sayısını artırma
            >>> post = post_repo._increment(
            ...     session,
            ...     record_id="post456",
            ...     field="like_count",
            ...     amount=1,
            ...     updated_by="user789"
            ... )
            
            >>> # Stock quantity güncelleme (10 adet ekle)
            >>> product = product_repo._increment(
            ...     session,
            ...     record_id="prod123",
            ...     field="stock_quantity",
            ...     amount=10,
            ...     updated_by="warehouse_system"
            ... )
            
            >>> # Float artırma (rating calculation)
            >>> user = user_repo._increment(
            ...     session,
            ...     record_id="user123",
            ...     field="total_score",
            ...     amount=4.5
            ... )
        
        Note:
            - Eğer alan None ise, amount değeri set edilir
            - Atomik işlem olarak gerçekleşir (flush kullanır)
            - updated_at otomatik güncellenir (model'de varsa)
            - Race condition'a karşı dikkatli olun (database-level increment yerine)
        """
        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True)
        
        if not hasattr(obj, field):
            raise DatabaseValidationError()
        
        current_value = getattr(obj, field)
        
        # Validate that field is numeric
        if current_value is None:
            new_value = amount
        elif isinstance(current_value, (int, float)):
            new_value = current_value + amount
        else:
            raise DatabaseValidationError()
        
        setattr(obj, field, new_value)
        
        if updated_by and hasattr(self.model, 'updated_by'):
            setattr(obj, 'updated_by', updated_by)
        
        session.add(obj)
        session.flush()
        return obj

    @_handle_db_exceptions
    def _decrement(
        self,
        session: Session,
        *,
        record_id: str,
        field: str,
        amount: Union[int, float] = 1,
        updated_by: Optional[str] = None,
        allow_negative: bool = False
    ) -> ModelType:
        """
        Sayısal bir alanı belirtilen miktarda azaltır (atomik).
        
        Sayısal bir alanı atomik olarak azaltır. Stock, credit, quota gibi
        sayısal kaynaklar için kullanılır. Negatif değerlere izin verilebilir.
        
        Args:
            session (Session): Veritabanı oturumu
            record_id (str): Güncellenecek kaydın ID'si
            field (str): Azaltılacak sayısal alanın adı
            amount (Union[int, float]): Azaltılacak miktar. Varsayılan: 1
            updated_by (Optional[str]): İşlemi yapan kullanıcının ID'si
            allow_negative (bool): Negatif değerlere izin ver. Varsayılan: False
        
        Returns:
            ModelType: Güncellenmiş model instance
        
        Raises:
            DatabaseValidationError: Kayıt bulunamazsa
            DatabaseValidationError: Alan mevcut değilse
            DatabaseValidationError: Alan sayısal değilse
            DatabaseValidationError: Sonuç negatif olacak ama allow_negative=False ise
            DatabaseValidationError: Alan None ve allow_negative=False ise
            DatabaseError: Diğer veritabanı hataları
        
        Examples:
            >>> # Stock azaltma (satın alma)
            >>> product = product_repo._decrement(
            ...     session,
            ...     record_id="prod123",
            ...     field="stock_quantity",
            ...     amount=5,
            ...     updated_by="order_system"
            ... )
            >>> print(f"Kalan stock: {product.stock_quantity}")
            
            >>> # Credit harcama (negatife izin yok)
            >>> user = user_repo._decrement(
            ...     session,
            ...     record_id="user456",
            ...     field="credits",
            ...     amount=10,
            ...     allow_negative=False  # Yetersiz bakiye hatası verir
            ... )
            
            >>> # Balance azaltma (negatife izin var - kredi/borç)
            >>> account = account_repo._decrement(
            ...     session,
            ...     record_id="acc789",
            ...     field="balance",
            ...     amount=100.50,
            ...     allow_negative=True,  # Eksi bakiyeye gidebilir
            ...     updated_by="payment_system"
            ... )
            >>> print(f"Bakiye: {account.balance}")  # -50.25 olabilir
            
            >>> # API quota azaltma
            >>> api_key = api_key_repo._decrement(
            ...     session,
            ...     record_id="key123",
            ...     field="remaining_requests",
            ...     amount=1
            ... )
        
        Note:
            - allow_negative=False: Sonuç < 0 olacaksa hata fırlatır (varsayılan)
            - allow_negative=True: Negatif değere gidebilir (bakiye/kredi sistemleri için)
            - Eğer alan None ise:
              * allow_negative=True: -amount değeri set edilir
              * allow_negative=False: Hata fırlatır
            - Atomik işlem olarak gerçekleşir (flush kullanır)
            - updated_at otomatik güncellenir (model'de varsa)
        
        Warning:
            Stock kontrolü gibi kritik durumlarda allow_negative=False kullanın!
            Negatif stock istemezsiniz.
        """
        obj = self._get_by_id(session, record_id=record_id, raise_not_found=True)
        
        if not hasattr(obj, field):
            raise DatabaseValidationError()
        
        current_value = getattr(obj, field)
        
        # Validate that field is numeric
        if current_value is None:
            if allow_negative:
                new_value = -amount
            else:
                raise DatabaseValidationError()
        elif isinstance(current_value, (int, float)):
            new_value = current_value - amount
            
            # Check for negative values if not allowed
            if not allow_negative and new_value < 0:
                raise DatabaseValidationError()
        else:
            raise DatabaseValidationError()
        
        setattr(obj, field, new_value)
        
        if updated_by and hasattr(self.model, 'updated_by'):
            setattr(obj, 'updated_by', updated_by)
        
        session.add(obj)
        session.flush()
        return obj

    # ============================================================================
    # SESSION MANAGEMENT & TRANSACTION CONTROL
    # ============================================================================
    """SESSION YÖNETİMİ VE TRANSACTION KONTROLÜ
    
    Bu repository'deki tüm metodlar flush() kullanır ancak commit() KULLANMAZ.
    Bu tasarım, transaction kontrolünü üst katmanlara (Service Layer) bırakarak
    maksimum esneklik sağlar.
    
    
    🎯 TASARIM PRENSİBİ:
    ═══════════════════════════════════════════════════════════════════════
    
    Repository Layer (Bu Sınıf):
        - CRUD operasyonlarını gerçekleştirir
        - session.flush() kullanır (değişiklikleri veritabanına gönderir)
        - session.commit() KULLANMAZ (transaction yönetimi yapmaz)
        - Transaction-agnostic (transaction'dan bağımsız) çalışır
    
    Service Layer (Üst Katman):
        - Business logic'i yönetir
        - Transaction sınırlarını belirler
        - session.commit() veya session.rollback() çağırır
        - @with_session veya @with_transaction decorator'larını kullanır
    
    
    📚 KULLANIM ŞEKİLLERİ:
    ═══════════════════════════════════════════════════════════════════════
    
    
    ✅ 1. DECORATOR İLE (ÖNERİLEN - EN KOLAY)
    ───────────────────────────────────────────────────────────────────────
    
    from database.engine.decorators import with_session, with_transaction
    
    # Tek işlem - Otomatik commit
    @with_session(auto_commit=True)
    def create_user_simple(session, name, email):
        user = user_repo._create(session, name=name, email=email)
        return user  # Decorator çıkışta otomatik commit yapar
    
    # Çoklu işlem - Atomic transaction
    @with_transaction()
    def create_user_with_profile(session, user_data, profile_data):
        # Hata olursa her ikisi de rollback edilir (atomic)
        user = user_repo._create(session, **user_data)
        profile_data['user_id'] = user.id
        profile = profile_repo._create(session, **profile_data)
        return user, profile  # Her ikisi de başarılı olursa commit
    
    # Read-only işlemler - Optimize
    @with_readonly_session()
    def get_all_users(session):
        return user_repo._get_all(session, limit=100)
        # auto_commit=False, auto_flush=False (performans)
    
    
    ✅ 2. CONTEXT MANAGER İLE (MANUEL KONTROL)
    ───────────────────────────────────────────────────────────────────────
    
    from database.engine.manager import get_database_manager
    
    manager = get_database_manager()
    
    # Otomatik commit
    with manager.engine.session_context(auto_commit=True) as session:
        user = user_repo._create(session, name="John", email="john@test.com")
        # Context manager çıkışta otomatik commit yapar
    
    # Manuel commit (daha fazla kontrol)
    with manager.engine.session_context(auto_commit=False) as session:
        try:
            # Birden fazla işlem
            user = user_repo._create(session, name="John", email="john@test.com")
            profile = profile_repo._create(session, user_id=user.id, bio="...")
            address = address_repo._create(session, user_id=user.id, city="...")
            
            # Hepsi başarılıysa commit
            session.commit()
            
        except Exception as e:
            # Hata varsa rollback (otomatik yapılır ama explicit de yapılabilir)
            session.rollback()
            raise
    
    
    ✅ 3. SERVICE LAYER PATTERN (PRODUCTION - EN İYİ UYGULAMA)
    ───────────────────────────────────────────────────────────────────────
    
    # services/user_service.py
    
    from database.engine.decorators import with_session, with_transaction
    from database.repositories.base_repository import BaseRepository
    
    class UserService:
        '''
        Service Layer: Business logic ve transaction yönetimi burada.
        Repository'leri kullanır ama direkt veritabanı işlemi yapmaz.
        '''
        
        def __init__(self):
            self.user_repo = BaseRepository(User)
            self.profile_repo = BaseRepository(Profile)
            self.notification_repo = BaseRepository(Notification)
        
        @with_session(auto_commit=True)
        def create_user(self, session, name: str, email: str) -> User:
            '''Basit kullanıcı oluşturma - tek işlem'''
            return self.user_repo._create(session, name=name, email=email)
        
        @with_transaction()
        def register_user(
            self, 
            session, 
            user_data: dict, 
            profile_data: dict
        ) -> tuple[User, Profile]:
            '''
            Kullanıcı kaydı - atomic transaction.
            User ve Profile birlikte oluşturulur.
            Herhangi biri başarısız olursa her ikisi de rollback.
            '''
            # 1. Kullanıcı oluştur
            user = self.user_repo._create(session, **user_data)
            
            # 2. Profile oluştur
            profile_data['user_id'] = user.id
            profile = self.profile_repo._create(session, **profile_data)
            
            # 3. Hoşgeldin bildirimi oluştur
            self.notification_repo._create(
                session,
                user_id=user.id,
                message=f"Hoşgeldin {user.name}!"
            )
            
            # Decorator otomatik commit yapar
            # Hata varsa otomatik rollback
            return user, profile
        
        @with_transaction()
        def transfer_money(
            self, 
            session, 
            from_user_id: str, 
            to_user_id: str, 
            amount: float
        ) -> tuple[User, User]:
            '''
            Para transferi - kritik atomic transaction.
            Her ikisi de başarılı olmalı, yoksa hiçbiri yapılmamalı.
            '''
            # 1. Gönderen hesabı bul ve güncelle
            sender = self.user_repo._get_by_id(session, record_id=from_user_id)
            if sender.balance < amount:
                raise ValueError("Yetersiz bakiye")
            
            sender_updated = self.user_repo._update(
                session,
                record_id=from_user_id,
                balance=sender.balance - amount
            )
            
            # 2. Alıcı hesabı bul ve güncelle
            receiver = self.user_repo._get_by_id(session, record_id=to_user_id)
            receiver_updated = self.user_repo._update(
                session,
                record_id=to_user_id,
                balance=receiver.balance + amount
            )
            
            # 3. İşlem kaydı oluştur
            self.transaction_repo._create(
                session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                status="completed"
            )
            
            # Tüm işlemler başarılı → commit
            # Herhangi biri başarısız → rollback
            return sender_updated, receiver_updated
        
        @with_session(auto_commit=False)
        def bulk_import_users(self, session, users_data: list[dict]) -> list[User]:
            '''
            Toplu kullanıcı ekleme - manuel commit için optimize.
            Her kayıt için ayrı commit yapmak yerine tek commit (performanslı).
            '''
            created_users = []
            
            for user_data in users_data:
                user = self.user_repo._create(session, **user_data)
                created_users.append(user)
            
            # Tüm kayıtları bir kerede commit
            session.commit()
            
            return created_users
        
        @with_readonly_session()
        def get_user_dashboard(self, session, user_id: str) -> dict:
            '''Read-only işlemler için optimize'''
            user = self.user_repo._get_by_id(session, record_id=user_id)
            posts = self.post_repo._get_all(session, user_id=user_id, limit=10)
            notifications = self.notification_repo._count(session, user_id=user_id, is_read=False)
            
            return {
                'user': user,
                'recent_posts': posts,
                'unread_notifications': notifications
            }
    
    
    # API/Controller Layer
    
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    router = APIRouter()
    user_service = UserService()
    
    class UserCreateRequest(BaseModel):
        name: str
        email: str
    
    @router.post("/users")
    def create_user_endpoint(request: UserCreateRequest):
        '''
        API endpoint - Service layer'ı çağırır.
        Session yönetimi service layer'da.
        '''
        try:
            user = user_service.create_user(
                name=request.name,
                email=request.email
            )
            return {"user_id": user.id, "message": "User created"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    
    ❌ 4. YANLIŞ KULLANIM (YAPMAYIN!)
    ───────────────────────────────────────────────────────────────────────
    
    # ❌ Session direkt kullanımı - commit unutulabilir
    session = engine.get_session()
    user = user_repo._create(session, name="John", email="john@test.com")
    # ⚠️ HATA: commit() yapılmadı! Kayıt kaybolur!
    session.close()
    
    # ✅ DOĞRUSU: Context manager veya decorator kullan
    with engine.session_context(auto_commit=True) as session:
        user = user_repo._create(session, name="John", email="john@test.com")
    
    
    🔍 FLUSH vs COMMIT FARKI
    ═══════════════════════════════════════════════════════════════════════
    
    flush():
        - Değişiklikleri veritabanına GÖNDERIR
        - Henüz transaction commit edilmez
        - ID'ler generate edilir (database tarafından)
        - Constraint kontrolleri yapılır
        - Rollback hala mümkün
        - Kullanım: session.flush()
    
    commit():
        - Transaction'ı TAMAMLAR
        - Değişiklikler kalıcı hale gelir
        - Rollback artık mümkün değil
        - Session temizlenir
        - Kullanım: session.commit()
    
    Örnek:
        user = user_repo._create(session, name="John")  # flush() yapıldı
        print(user.id)  # ID mevcut (database generate etti)
        # ⚠️ Henüz commit yapılmadı, rollback edilebilir!
        
        session.commit()  # Artık kalıcı
        # ✅ Rollback artık mümkün değil
    
    
    🎯 NE ZAMAN HANGİ YAKLAŞIM?
    ═══════════════════════════════════════════════════════════════════════
    
    @with_session(auto_commit=True):
        ✅ Tek bir repository metodu çağrısı
        ✅ Basit CRUD işlemleri
        ✅ Hızlı prototipleme
    
    @with_transaction():
        ✅ Birden fazla repository metodu (atomic gerekli)
        ✅ Para transferi, sipariş işlemleri gibi kritik işlemler
        ✅ Business logic içeren işlemler
    
    @with_readonly_session():
        ✅ Sadece okuma işlemleri
        ✅ Raporlama, dashboard'lar
        ✅ Performans kritik sorgular
    
    Context Manager (auto_commit=False):
        ✅ Karmaşık transaction logic
        ✅ Conditional commit (bazı durumlarda commit, bazı durumlarda rollback)
        ✅ Bulk operations (tek commit ile binlerce kayıt)
    
    
    ⚠️ DİKKAT EDİLMESİ GEREKENLER
    ═══════════════════════════════════════════════════════════════════════
    
    1. Repository metodları transaction-agnostic'tir:
       - Kendi başlarına transaction başlatmazlar
       - commit() çağırmazlar
       - Session'ı kapatmazlar
    
    2. Her repository metodu çağrısından sonra:
       - Değişiklikler flush() ile veritabanına gönderilir
       - Ancak henüz commit edilmez
       - Rollback hala mümkündür
    
    3. Decorator veya Context Manager çıkışında:
       - auto_commit=True ise otomatik commit yapılır
       - auto_commit=False ise manuel commit gerekir
       - Hata varsa otomatik rollback yapılır
    
    4. Nested transactions için:
       - @with_transaction(savepoint=True) kullanın
       - SAVEPOINT ile partial rollback yapılabilir
    
    5. Long-running transactions'dan kaçının:
       - Database lock'ları uzun süre tutulur
       - Deadlock riski artar
       - İşlemleri küçük parçalara bölün
    
    
    📖 DAHA FAZLA BİLGİ
    ═══════════════════════════════════════════════════════════════════════
    
    - Decorator dokümantasyonu: database/engine/decorators.py
    - Engine dokümantasyonu: database/engine/engine.py
    - Örnekler: examples/04_session_management.py
    - Service Layer örnekleri: examples/11_production_architecture.py
    """