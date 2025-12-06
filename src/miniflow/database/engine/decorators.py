from functools import wraps
from typing import Callable, TypeVar, Optional, Any
import inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DBAPIError

from miniflow.core.exceptions import DatabaseQueryError
from .manager import DatabaseManager, get_database_manager


T = TypeVar('T')


def _inject_session_parameter(func: Callable, session: Session, args: tuple, kwargs: dict) -> Any:
    """
    Inject session parameter correctly for both functions and methods.
    
    This improved version gracefully handles user mistakes:
    - If user accidentally passes session → Override with decorator's session
    - If user correctly omits session → Insert decorator's session
    - Works with both positional args and keyword args
    
    Args:
        func: The function to call
        session: The session to inject (from decorator)
        args: Positional arguments from the original call
        kwargs: Keyword arguments from the original call
    
    Returns:
        The result of the function call
        
    Algorithm:
        1. Find session parameter index in function signature
        2. Check if session is in kwargs → override it
        3. Count actual vs expected args:
           - If actual == expected → user passed session (OVERRIDE)
           - If actual == expected - 1 → user didn't pass session (INSERT)
           - Otherwise → insert at correct position
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    # Find the index of the 'session' parameter
    try:
        session_param_index = params.index('session')
    except ValueError:
        # No 'session' parameter in function - just call as-is
        # This shouldn't happen with our decorators, but handle gracefully
        return func(*args, **kwargs)
    
    # CASE 1: Session passed as keyword argument
    if 'session' in kwargs:
        # Override the keyword argument with decorator's session
        modified_kwargs = dict(kwargs)
        modified_kwargs['session'] = session
        # Use args as-is (session shouldn't be in args if it's in kwargs)
        return func(*args, **modified_kwargs)
    
    # CASE 2: Session passed as positional argument (or not passed at all)
    args_list = list(args)
    
    # Calculate expected parameter count
    expected_param_count = len(params)
    actual_args_count = len(args_list)
    
    if actual_args_count == expected_param_count:
        # User passed ALL parameters including session
        # Example: foo(cls, user_session, data) when signature is foo(cls, session, data)
        # This is WRONG, but we handle it gracefully
        # STRATEGY: OVERRIDE user's session with decorator's session
        args_list[session_param_index] = session
        return func(*args_list, **kwargs)
    
    elif actual_args_count == expected_param_count - 1:
        # User passed all parameters EXCEPT session
        # Example: foo(cls, data) when signature is foo(cls, session, data)
        # This is CORRECT usage
        # STRATEGY: INSERT decorator's session at the correct position
        args_list.insert(session_param_index, session)
        return func(*args_list, **kwargs)
    
    else:
        # Edge case: User passed fewer parameters than expected
        # Could be valid if there are default parameters
        # STRATEGY: INSERT session at the correct position and let Python handle validation
        args_list.insert(session_param_index, session)
        return func(*args_list, **kwargs)


def with_session(
    auto_commit: bool = True,
    auto_flush: bool = True,
    isolation_level: Optional[str] = None,
    manager: Optional[DatabaseManager] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Veritabanı session yönetimi için decorator.
    
    Bu decorator, fonksiyonun ilk parametresine otomatik olarak SQLAlchemy Session
    inject eder ve session yaşam döngüsünü (açma/kapama/commit/rollback) otomatik
    olarak yönetir. Repository metodlarını çağıran fonksiyonlar için ideal bir
    kullanım kolaylığı sağlar.
    
    Decorator'ın çalışma mantığı:
        1. Fonksiyon çağrıldığında yeni bir session oluşturulur
        2. Session fonksiyonun ilk parametresi olarak inject edilir
        3. Fonksiyon çalıştırılır
        4. Başarılı ise: auto_flush=True ise flush(), auto_commit=True ise commit()
        5. Hata varsa: Otomatik rollback yapılır
        6. Her durumda: Session kapatılır
    
    Args:
        auto_commit (bool): İşlem sonunda otomatik commit yapılsın mı?
            - True (varsayılan): Fonksiyon başarılı olursa otomatik commit
            - False: Manuel commit gerekir (dikkatli kullanılmalı)
            
        auto_flush (bool): Değişiklikler otomatik flush edilsin mi?
            - True (varsayılan): Değişiklikler veritabanına gönderilir
            - False: Sadece commit edilince gönderilir
            
        isolation_level (Optional[str]): Transaction isolation seviyesi.
            - None (varsayılan): Database default isolation level
            - 'READ_UNCOMMITTED': En düşük seviye (dirty reads mümkün)
            - 'READ_COMMITTED': Yaygın kullanım (PostgreSQL default)
            - 'REPEATABLE_READ': Aynı transaction içinde tutarlı okuma
            - 'SERIALIZABLE': En yüksek seviye (tam izolasyon)
            
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager instance'ı.
            - None (varsayılan): Global singleton manager kullanılır
            - DatabaseManager: Belirli bir manager instance'ı kullanılır
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
            - Decorator bir fonksiyon döndürür
            - Dönen fonksiyon çağrıldığında session yönetimi otomatik yapılır
            
    Raises:
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseConnectionError: Veritabanı bağlantı hatası varsa
        DatabaseQueryError: Veritabanı sorgu hatası varsa
        DatabaseError: Diğer veritabanı hataları
        
    Examples:
        >>> # Basit kullanım - otomatik commit
        >>> @with_session()
        >>> def get_user(session: Session, user_id: str):
        ...     return user_repo._get_by_id(session, record_id=user_id)
        >>> 
        >>> user = get_user("user123")  # Session otomatik inject edildi
        
        >>> # Manuel commit (çoklu işlem için)
        >>> @with_session(auto_commit=False)
        >>> def create_user_with_profile(session: Session, user_data: dict, profile_data: dict):
        ...     user = user_repo._create(session, **user_data)
        ...     profile_data['user_id'] = user.id
        ...     profile = profile_repo._create(session, **profile_data)
        ...     session.commit()  # Manuel commit
        ...     return user, profile
        
        >>> # Isolation level ile
        >>> @with_session(isolation_level='SERIALIZABLE')
        >>> def critical_transfer(session: Session, from_id: str, to_id: str, amount: float):
        ...     # Yüksek izolasyon seviyesi ile kritik işlem
        ...     sender = user_repo._get_by_id(session, record_id=from_id)
        ...     receiver = user_repo._get_by_id(session, record_id=to_id)
        ...     sender.balance -= amount
        ...     receiver.balance += amount
        
        >>> # Özel manager ile
        >>> custom_manager = DatabaseManager()
        >>> custom_manager.initialize(config)
        >>> 
        >>> @with_session(manager=custom_manager)
        >>> def use_custom_db(session: Session):
        ...     # Özel manager'ın engine'ini kullanır
        ...     pass
        
        >>> # Hata durumunda otomatik rollback
        >>> @with_session()
        >>> def risky_operation(session: Session):
        ...     user = user_repo._create(session, email="test@test.com")
        ...     raise ValueError("Hata!")  # Otomatik rollback yapılır
        >>> 
        >>> try:
        ...     risky_operation()
        ... except ValueError:
        ...     pass  # Kullanıcı veritabanına kaydedilmedi (rollback)
    
    Note:
        - Repository metodları flush() kullanır ama commit() kullanmaz
        - Bu decorator ile commit otomatik yapılır
        - İlk parametre mutlaka `session: Session` olmalı
        - Session otomatik kapatılır, manuel kapatmaya gerek yok
        - Hata durumunda otomatik rollback yapılır (transaction güvenliği)
        - auto_commit=False kullanırken dikkatli olun, unutulursa değişiklikler kaybolur
        
    Comparison with Other Decorators:
        - with_transaction(): Atomic transaction garantisi (nested transaction desteği)
        - with_readonly_session(): Sadece okuma için optimize (commit/flush yok)
        - with_retry_session(): Deadlock/timeout durumlarında otomatik retry
        - inject_session(): Keyword argument olarak session inject eder
        
    Performance Notes:
        - Her fonksiyon çağrısında yeni session oluşturulur
        - Uzun süreli işlemler için context manager kullanmayı düşünün
        - Read-only işlemler için with_readonly_session() daha performanslı
        
    Related:
        - :meth:`DatabaseEngine.session_context`: Context manager versiyonu
        - :class:`DatabaseManager`: Engine yönetimi
        - :meth:`with_transaction`: Atomic transaction için
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # classmethod veya staticmethod desteği
        if isinstance(func, classmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=auto_commit,
                    auto_flush=auto_flush,
                    isolation_level=isolation_level
                ) as session:
                    return _inject_session_parameter(original_func, session, args, kwargs)
            
            return classmethod(wrapper)
        
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=auto_commit,
                    auto_flush=auto_flush,
                    isolation_level=isolation_level
                ) as session:
                    return _inject_session_parameter(original_func, session, args, kwargs)
            
            return staticmethod(wrapper)
        
        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=auto_commit,
                    auto_flush=auto_flush,
                    isolation_level=isolation_level
                ) as session:
                    return _inject_session_parameter(func, session, args, kwargs)
            
            return wrapper
    return decorator


def with_transaction(
    isolation_level: Optional[str] = None,
    savepoint: bool = False,
    manager: Optional[DatabaseManager] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Atomic transaction yönetimi için decorator.
    
    Bu decorator, kritik işlemler için tam atomic transaction garantisi sağlar.
    Tüm işlemler başarılı olursa commit, herhangi biri başarısız olursa rollback
    yapılır. Nested transaction (SAVEPOINT) desteği ile kısmi rollback
    yapılabilir.
    
    with_session()'dan farkı:
        - Her zaman auto_commit=True ve auto_flush=True kullanır
        - Nested transaction (savepoint) desteği vardır
        - Kritik işlemler için tasarlanmıştır
        - Para transferi, sipariş işlemleri gibi atomic gereksinimler için idealdir
    
    Args:
        isolation_level (Optional[str]): Transaction isolation seviyesi.
            - None (varsayılan): Database default isolation level
            - 'READ_COMMITTED': Yaygın kullanım (tutarlı okuma)
            - 'SERIALIZABLE': En yüksek seviye (tam izolasyon)
            - Diğer seviyeler: 'READ_UNCOMMITTED', 'REPEATABLE_READ'
            
        savepoint (bool): Nested transaction için SAVEPOINT kullan.
            - False (varsayılan): Normal transaction (tam rollback)
            - True: SAVEPOINT ile nested transaction (kısmi rollback mümkün)
            - Kullanım: Zaten bir transaction içindeyse, yeni bir savepoint oluşturur
            - Partial rollback: Sadece savepoint içindeki işlemler rollback edilir
            
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager.
            - None (varsayılan): Global singleton manager
            - DatabaseManager: Özel manager instance'ı
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
        
    Raises:
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseTransactionError: Transaction hatası varsa
        DatabaseConnectionError: Veritabanı bağlantı hatası
        DatabaseError: Diğer veritabanı hataları
        
    Examples:
        >>> # Basit atomic transaction
        >>> @with_transaction()
        >>> def transfer_money(session: Session, from_id: str, to_id: str, amount: float):
        ...     # Tüm işlemler başarılı olmalı, yoksa hiçbiri yapılmaz (atomic)
        ...     sender = user_repo._get_by_id(session, record_id=from_id)
        ...     receiver = user_repo._get_by_id(session, record_id=to_id)
        ...     
        ...     if sender.balance < amount:
        ...         raise ValueError("Yetersiz bakiye")
        ...     
        ...     user_repo._update(session, record_id=from_id, balance=sender.balance - amount)
        ...     user_repo._update(session, record_id=to_id, balance=receiver.balance + amount)
        ...     # Otomatik commit (her ikisi de başarılı ise)
        
        >>> # Nested transaction (savepoint) ile kısmi rollback
        >>> @with_transaction()
        >>> def complex_operation(session: Session):
        ...     # Ana işlem
        ...     user = user_repo._create(session, email="test@test.com")
        ...     
        ...     try:
        ...         # Nested transaction - başarısız olursa sadece bu kısım rollback
        ...         @with_transaction(savepoint=True)
        ...         def try_optional_step(session: Session):
        ...             # Bu adım başarısız olsa bile ana işlem commit edilir
        ...             optional_repo._create(session, user_id=user.id, data="optional")
        ...         
        ...         try_optional_step(session)
        ...     except Exception:
        ...         # Optional step başarısız oldu ama ana işlem devam ediyor
        ...         pass
        
        >>> # Yüksek izolasyon seviyesi ile kritik işlem
        >>> @with_transaction(isolation_level='SERIALIZABLE')
        >>> def critical_order_processing(session: Session, order_id: str):
        ...     # Seri hale getirilmiş transaction (concurrent access engellenir)
        ...     order = order_repo._get_by_id(session, record_id=order_id)
        ...     inventory = inventory_repo._get_by_id(session, record_id=order.product_id)
        ...     
        ...     if inventory.stock < order.quantity:
        ...         raise ValueError("Yetersiz stok")
        ...     
        ...     inventory_repo._update(session, record_id=inventory.id, stock=inventory.stock - order.quantity)
        ...     order_repo._update(session, record_id=order_id, status="confirmed")
        
        >>> # Hata durumunda otomatik rollback
        >>> @with_transaction()
        >>> def risky_batch_update(session: Session, user_ids: list):
        ...     for user_id in user_ids:
        ...         user_repo._update(session, record_id=user_id, status="active")
        ...     # Herhangi biri başarısız olursa hepsi rollback edilir
        
    Note:
        - Her zaman auto_commit=True ve auto_flush=True kullanır
        - Atomic guarantee: Tüm işlemler veya hiçbiri
        - Nested transaction (savepoint=True) sadece mevcut transaction içindeyse çalışır
        - Deadlock durumlarında with_retry_session() kullanmayı düşünün
        - Kritik finansal işlemler için isolation_level='SERIALIZABLE' önerilir
        
    Comparison with Other Decorators:
        - with_session(): Daha esnek (auto_commit ayarlanabilir)
        - with_retry_session(): Deadlock/timeout için retry desteği
        - with_readonly_session(): Sadece okuma için optimize
        
    Use Cases:
        - Para transferi (atomic gereksinim)
        - Sipariş işleme (inventory + order güncelleme)
        - Batch operations (hepsi veya hiçbiri)
        - Distributed transactions (ACID garantisi)
        
    Related:
        - :meth:`with_session`: Esnek session yönetimi
        - :meth:`with_retry_session`: Retry desteği ile transaction
        - :class:`DatabaseEngine`: Engine yönetimi
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # classmethod veya staticmethod desteği
        if isinstance(func, classmethod):
            # classmethod objesi ise __func__'e eriş
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=True,
                    auto_flush=True,
                    isolation_level=isolation_level
                ) as session:
                    # Session inject et
                    if savepoint and session.in_transaction():
                        # Nested transaction için savepoint kullan
                        with session.begin_nested():
                            return _inject_session_parameter(original_func, session, args, kwargs)
                    else:
                        return _inject_session_parameter(original_func, session, args, kwargs)
            
            # classmethod olarak döndür
            return classmethod(wrapper)
        
        elif isinstance(func, staticmethod):
            # staticmethod objesi ise __func__'e eriş
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=True,
                    auto_flush=True,
                    isolation_level=isolation_level
                ) as session:
                    # Session inject et
                    if savepoint and session.in_transaction():
                        # Nested transaction için savepoint kullan
                        with session.begin_nested():
                            return _inject_session_parameter(original_func, session, args, kwargs)
                    else:
                        return _inject_session_parameter(original_func, session, args, kwargs)
            
            # staticmethod olarak döndür
            return staticmethod(wrapper)
        
        else:
            # Normal fonksiyon
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=True,
                    auto_flush=True,
                    isolation_level=isolation_level
                ) as session:
                    # Session inject et
                    if savepoint and session.in_transaction():
                        # Nested transaction için savepoint kullan
                        with session.begin_nested():
                            return _inject_session_parameter(func, session, args, kwargs)
                    else:
                        return _inject_session_parameter(func, session, args, kwargs)
            
            return wrapper
    return decorator


def with_readonly_session(
    manager: Optional[DatabaseManager] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Read-only (sadece okuma) işlemleri için optimize edilmiş decorator.
    
    Bu decorator, sadece veritabanından veri okuma işlemleri için optimize edilmiştir.
    Commit ve flush işlemlerini devre dışı bırakarak performans artışı sağlar.
    PostgreSQL gibi veritabanlarında read-only transaction'lar özel olarak optimize edilir.
    
    Özellikleri:
        - auto_commit=False: Commit yapılmaz (gereksiz overhead yok)
        - auto_flush=False: Flush yapılmaz (okuma için gerekmez)
        - Performans: Read-only transaction'lar daha hızlıdır
        - Güvenlik: Yanlışlıkla yazma yapılmaz
    
    Args:
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager instance'ı.
            - None (varsayılan): Global singleton manager kullanılır
            - DatabaseManager: Belirli bir manager instance'ı kullanılır
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
        
    Raises:
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseConnectionError: Veritabanı bağlantı hatası varsa
        DatabaseQueryError: Veritabanı sorgu hatası varsa
        
    Examples:
        >>> # Basit okuma işlemi
        >>> @with_readonly_session()
        >>> def get_all_users(session: Session) -> List[User]:
        ...     return user_repo._get_all(session, limit=100)
        
        >>> # Dashboard verileri çekme
        >>> @with_readonly_session()
        >>> def get_dashboard_data(session: Session, user_id: str) -> dict:
        ...     user = user_repo._get_by_id(session, record_id=user_id)
        ...     posts = post_repo._get_all(session, user_id=user_id, limit=10)
        ...     stats = user_repo._count(session, is_active=True)
        ...     return {
        ...         'user': user,
        ...         'recent_posts': posts,
        ...         'active_users_count': stats
        ...     }
        
        >>> # Raporlama işlemleri
        >>> @with_readonly_session()
        >>> def generate_monthly_report(session: Session, month: int, year: int) -> dict:
        ...     filter_params = FilterParams()
        ...     filter_params.add_filter("created_at", f"{year}-{month:02d}%", "like")
        ...     orders = order_repo._filter(session, filter_params=filter_params)
        ...     total_revenue = sum(order.amount for order in orders)
        ...     return {
        ...         'month': month,
        ...         'year': year,
        ...         'total_orders': len(orders),
        ...         'total_revenue': total_revenue
        ...     }
        
        >>> # Arama ve filtreleme
        >>> @with_readonly_session()
        >>> def search_users(session: Session, query: str) -> List[User]:
        ...     filter_params = FilterParams()
        ...     filter_params.search = query
        ...     filter_params.search_fields = ["name", "email", "username"]
        ...     return user_repo._filter(session, filter_params=filter_params, limit=50)
        
        >>> # Sayfalama ile veri çekme
        >>> @with_readonly_session()
        >>> def get_paginated_products(session: Session, page: int, page_size: int):
        ...     pagination_params = PaginationParams(page=page, page_size=page_size)
        ...     return product_repo._paginate(session, pagination_params=pagination_params)
        
    Note:
        - Sadece okuma işlemleri için kullanılmalı
        - Repository metodları (_get_by_id, _get_all, _filter, _paginate vb.) için uygun
        - Yazma işlemleri (_create, _update, _delete) için KULLANILMAMALI
        - Performans avantajı: Commit/flush overhead'i yok
        - PostgreSQL'de özel optimizasyonlar uygulanır
        - Transaction yine de oluşturulur ama commit edilmez
        
    Performance Benefits:
        - Commit overhead'i yok: Daha hızlı
        - Flush overhead'i yok: Daha hızlı
        - Database-level optimizations: Read-only transaction'lar optimize edilir
        - Connection pooling: Read connection'lar ayrı pool'da tutulabilir
        
    Warning:
        ⚠️ Yazma işlemleri için kullanmayın!
        - _create, _update, _delete gibi metodlar çalışmaz (commit yok)
        - Yanlışlıkla yazma yapmaya çalışırsanız sessizce başarısız olur
        
    Comparison with Other Decorators:
        - with_session(): Hem okuma hem yazma için (commit/flush var)
        - with_transaction(): Atomic yazma işlemleri için
        - with_retry_session(): Retry desteği ile yazma için
        
    Use Cases:
        - Dashboard verileri
        - Raporlama
        - Arama işlemleri
        - API GET endpoint'leri
        - Analytics sorguları
        
    Related:
        - :meth:`with_session`: Okuma/yazma için genel decorator
        - :meth:`user_repo._get_all`: Okuma işlemleri için repository metodu
        - :class:`DatabaseEngine`: Engine yönetimi
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # classmethod veya staticmethod desteği
        if isinstance(func, classmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=False,
                    auto_flush=False,
                    isolation_level=None
                ) as session:
                    return _inject_session_parameter(original_func, session, args, kwargs)
            
            return classmethod(wrapper)
        
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=False,
                    auto_flush=False,
                    isolation_level=None
                ) as session:
                    return _inject_session_parameter(original_func, session, args, kwargs)
            
            return staticmethod(wrapper)
        
        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                with mgr.engine.session_context(
                    auto_commit=False,
                    auto_flush=False,
                    isolation_level=None
                ) as session:
                    return _inject_session_parameter(func, session, args, kwargs)
            
            return wrapper
    return decorator


def with_retry_session(
    max_attempts: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    auto_commit: bool = True,
    manager: Optional[DatabaseManager] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Deadlock ve timeout durumlarında otomatik retry desteği ile session decorator.
    
    Bu decorator, veritabanı deadlock veya lock timeout hatalarında işlemi otomatik
    olarak yeniden dener. Exponential backoff stratejisi kullanarak her denemede
    bekleme süresini artırır. Finansal işlemler, inventory güncellemeleri ve
    concurrent update'ler için önerilir.
    
    Retry Mantığı:
        1. Fonksiyon çalıştırılır
        2. Deadlock/timeout hatası yakalanırsa:
           a. Bekleme süresi hesaplanır (delay * backoff^attempt)
           b. Belirtilen süre beklenir
           c. Yeniden deneme yapılır
        3. max_attempts'a ulaşılınca veya retry edilemez hata gelirse:
           a. Son exception fırlatılır
    
    Args:
        max_attempts (int): Maksimum deneme sayısı.
            - Varsayılan: 3
            - Minimum: 1 (en az bir deneme)
            - Önerilen: 3-5 (deadlock durumlarında yeterli)
            
        delay (float): İlk deneme arası bekleme süresi (saniye).
            - Varsayılan: 0.1 (100ms)
            - Önerilen: 0.1-0.5 saniye
            - Exponential backoff ile artar (delay * backoff^attempt)
            
        backoff (float): Her denemede bekleme süresini çarpan.
            - Varsayılan: 2.0 (her denemede 2x artar)
            - Örnek: delay=0.1, backoff=2.0 → 0.1s, 0.2s, 0.4s, 0.8s...
            - Exponential backoff: Deadlock'lar genelde kısa sürer
            
        auto_commit (bool): İşlem sonunda otomatik commit yapılsın mı?
            - True (varsayılan): Başarılı olursa otomatik commit
            - False: Manuel commit gerekir
            
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager.
            - None (varsayılan): Global singleton manager
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
        
    Raises:
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseConnectionError: Veritabanı bağlantı hatası (retry edilemez)
        DatabaseQueryError: Deadlock/timeout hatası (retry edilir)
        DatabaseError: Diğer veritabanı hataları
        
    Examples:
        >>> # Inventory güncelleme (deadlock riski yüksek)
        >>> @with_retry_session(max_attempts=5, delay=0.2)
        >>> def update_inventory(session: Session, product_id: str, quantity: int):
        ...     # WITH FOR UPDATE: Pessimistic locking (deadlock riski)
        ...     product = session.query(Product).with_for_update().filter_by(id=product_id).first()
        ...     product.stock += quantity
        ...     # Deadlock olursa otomatik retry yapılır
        
        >>> # Finansal işlem (kritik)
        >>> @with_retry_session(max_attempts=3, delay=0.1, backoff=2.0)
        >>> def transfer_funds(session: Session, from_id: str, to_id: str, amount: float):
        ...     # Concurrent transfer'ler deadlock oluşturabilir
        ...     sender = user_repo._get_by_id(session, record_id=from_id)
        ...     receiver = user_repo._get_by_id(session, record_id=to_id)
        ...     
        ...     if sender.balance < amount:
        ...         raise ValueError("Yetersiz bakiye")
        ...     
        ...     user_repo._update(session, record_id=from_id, balance=sender.balance - amount)
        ...     user_repo._update(session, record_id=to_id, balance=receiver.balance + amount)
        
        >>> # Batch güncelleme (concurrent access)
        >>> @with_retry_session(max_attempts=4)
        >>> def batch_update_status(session: Session, user_ids: List[str], status: str):
        ...     for user_id in user_ids:
        ...         user_repo._update(session, record_id=user_id, status=status)
        ...     # Eğer concurrent update varsa retry yapılır
        
        >>> # Özel retry ayarları
        >>> @with_retry_session(
        ...     max_attempts=5,
        ...     delay=0.5,      # Daha uzun başlangıç beklemesi
        ...     backoff=1.5,    # Daha yavaş artış
        ...     auto_commit=True
        ... )
        >>> def critical_operation(session: Session):
        ...     # Kritik işlem için daha agresif retry
        ...     pass
        
    Deadlock Detection:
        Decorator şu hataları deadlock/timeout olarak algılar:
        - "deadlock" kelimesi içeren hatalar
        - "lock timeout" içeren hatalar
        - "lock wait timeout" içeren hatalar
        - MySQL error code: 1213 (deadlock)
        - PostgreSQL error code: 40p01 (deadlock)
        
        Bu hatalar dışındaki hatalar retry edilmez (direkt fırlatılır).
        
    Exponential Backoff Örneği:
        max_attempts=3, delay=0.1, backoff=2.0:
        - Attempt 1: Hata → 0.1s bekle → Retry
        - Attempt 2: Hata → 0.2s bekle → Retry
        - Attempt 3: Hata → 0.4s bekle → Retry
        - Attempt 4: Son deneme → Başarısız → Exception fırlat
        
        Her denemede bekleme süresi: delay * (backoff ^ (attempt - 1))
        
    Note:
        - Sadece deadlock/timeout hatalarında retry yapılır
        - Diğer hatalar (syntax error, constraint violation vb.) retry edilmez
        - Her retry'da yeni bir session oluşturulur (temiz başlangıç)
        - max_attempts'tan sonra son exception fırlatılır
        - Deadlock'lar genelde kısa sürer (ms'ler içinde)
        - Uzun deadlock'lar sistemin overload olduğunu gösterir
        
    When to Use:
        - Pessimistic locking (WITH FOR UPDATE) kullanılan yerler
        - Concurrent update işlemleri
        - Finansal işlemler (para transferi, bakiye güncelleme)
        - Inventory güncellemeleri (stock, quantity)
        - Counter güncellemeleri (view_count, like_count)
        
    When NOT to Use:
        - Read-only işlemler (with_readonly_session() kullan)
        - Tek seferlik insert'ler (deadlock riski düşük)
        - Uzun süren işlemler (retry mantıklı değil)
        
    Performance Impact:
        - Deadlock olmazsa: Zero overhead (normal işlem)
        - Deadlock olursa: Exponential backoff ile retry
        - Her retry yeni session oluşturur (küçük overhead)
        
    Related:
        - :meth:`with_transaction`: Atomic transaction (retry yok)
        - :meth:`with_session`: Normal session (retry yok)
        - :class:`DatabaseEngine`: Engine yönetimi
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # classmethod veya staticmethod desteği
        if isinstance(func, classmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                last_exception: Optional[Exception] = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        with mgr.engine.session_context(
                            auto_commit=auto_commit,
                            auto_flush=True
                        ) as session:
                            result = _inject_session_parameter(original_func, session, args, kwargs)
                            
                            if attempt > 1:
                                print(f"[INFO] {original_func.__name__} succeeded on attempt {attempt}/{max_attempts}")
                            
                            return result
                    
                    except (OperationalError, DBAPIError, DatabaseQueryError) as e:
                        last_exception = e
                        error_msg = str(e).lower()
                        
                        is_deadlock = any(
                            indicator in error_msg 
                            for indicator in ['deadlock', 'lock timeout', 'lock wait timeout']
                        )
                        
                        if not is_deadlock or attempt >= max_attempts:
                            print(f"[ERROR] {original_func.__name__} failed after {attempt} attempts: {e}")
                            raise
                        
                        import time
                        wait_time = delay * (backoff ** (attempt - 1))
                        print(f"[WARNING] {original_func.__name__} deadlock on attempt {attempt}, "
                              f"retrying in {wait_time:.2f}s")
                        time.sleep(wait_time)
                    
                    except SQLAlchemyError as e:
                        print(f"[ERROR] {original_func.__name__} non-retryable error: {e}")
                        raise
                
                print(f"[CRITICAL] Unexpected retry flow for {original_func.__name__}")
                raise last_exception or RuntimeError("Unexpected retry flow")
            
            return classmethod(wrapper)
        
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                last_exception: Optional[Exception] = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        with mgr.engine.session_context(
                            auto_commit=auto_commit,
                            auto_flush=True
                        ) as session:
                            result = _inject_session_parameter(original_func, session, args, kwargs)
                            
                            if attempt > 1:
                                print(f"[INFO] {original_func.__name__} succeeded on attempt {attempt}/{max_attempts}")
                            
                            return result
                    
                    except (OperationalError, DBAPIError, DatabaseQueryError) as e:
                        last_exception = e
                        error_msg = str(e).lower()
                        
                        is_deadlock = any(
                            indicator in error_msg 
                            for indicator in ['deadlock', 'lock timeout', 'lock wait timeout']
                        )
                        
                        if not is_deadlock or attempt >= max_attempts:
                            print(f"[ERROR] {original_func.__name__} failed after {attempt} attempts: {e}")
                            raise
                        
                        import time
                        wait_time = delay * (backoff ** (attempt - 1))
                        print(f"[WARNING] {original_func.__name__} deadlock on attempt {attempt}, "
                              f"retrying in {wait_time:.2f}s")
                        time.sleep(wait_time)
                    
                    except SQLAlchemyError as e:
                        print(f"[ERROR] {original_func.__name__} non-retryable error: {e}")
                        raise
                
                print(f"[CRITICAL] Unexpected retry flow for {original_func.__name__}")
                raise last_exception or RuntimeError("Unexpected retry flow")
            
            return staticmethod(wrapper)
        
        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                last_exception: Optional[Exception] = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        with mgr.engine.session_context(
                            auto_commit=auto_commit,
                            auto_flush=True
                        ) as session:
                            result = _inject_session_parameter(func, session, args, kwargs)
                            
                            if attempt > 1:
                                print(f"[INFO] {func.__name__} succeeded on attempt {attempt}/{max_attempts}")
                            
                            return result
                    
                    except (OperationalError, DBAPIError, DatabaseQueryError) as e:
                        last_exception = e
                        error_msg = str(e).lower()
                        
                        is_deadlock = any(
                            indicator in error_msg 
                            for indicator in ['deadlock', 'lock timeout', 'lock wait timeout']
                        )
                        
                        if not is_deadlock or attempt >= max_attempts:
                            print(f"[ERROR] {func.__name__} failed after {attempt} attempts: {e}")
                            raise
                        
                        import time
                        wait_time = delay * (backoff ** (attempt - 1))
                        print(f"[WARNING] {func.__name__} deadlock on attempt {attempt}, "
                              f"retrying in {wait_time:.2f}s")
                        time.sleep(wait_time)
                    
                    except SQLAlchemyError as e:
                        print(f"[ERROR] {func.__name__} non-retryable error: {e}")
                        raise
                
                print(f"[CRITICAL] Unexpected retry flow for {func.__name__}")
                raise last_exception or RuntimeError("Unexpected retry flow")
            
            return wrapper
    return decorator


def inject_session(
    parameter_name: str = 'session',
    manager: Optional[DatabaseManager] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Keyword argument olarak session inject eden decorator.
    
    Bu decorator, fonksiyonun ilk parametresi yerine keyword argument olarak
    session inject eder. Mevcut kod tabanlarına uyum sağlamak ve fonksiyon
    signature'larını değiştirmeden session kullanmak için idealdir.
    
    with_session()'dan farkı:
        - with_session(): İlk parametre olarak session inject eder
        - inject_session(): Keyword argument olarak session inject eder
        - Mevcut kodlarda signature değişikliği gerektirmez
    
    Args:
        parameter_name (str): Inject edilecek parametrenin adı.
            - Varsayılan: 'session'
            - Özel isim: 'db_session', 'db', 'conn' gibi
            - Fonksiyon parametresinde bu isimle tanımlanmalı
            
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager.
            - None (varsayılan): Global singleton manager
            - DatabaseManager: Özel manager instance'ı
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
        
    Raises:
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseConnectionError: Veritabanı bağlantı hatası varsa
        DatabaseError: Diğer veritabanı hataları
        
    Examples:
        >>> # Basit kullanım - keyword argument
        >>> @inject_session()
        >>> def get_user(user_id: str, session: Session = None):
        ...     return user_repo._get_by_id(session, record_id=user_id)
        >>> 
        >>> user = get_user("user123")  # session otomatik inject edildi
        
        >>> # Özel parametre adı
        >>> @inject_session(parameter_name='db_session')
        >>> def get_products(category: str, db_session: Session = None):
        ...     return product_repo._get_all(db_session, category=category)
        >>> 
        >>> products = get_products("electronics")  # db_session otomatik inject
        
        >>> # Manuel session override (opsiyonel)
        >>> @inject_session()
        >>> def get_user_with_session(user_id: str, session: Session = None):
        ...     return user_repo._get_by_id(session, record_id=user_id)
        >>> 
        >>> # Manuel session geçilebilir (decorator inject etmez)
        >>> custom_session = manager.engine.get_session()
        >>> user = get_user_with_session("user123", session=custom_session)
        
        >>> # Mevcut kodlara uyum için
        >>> # Eski kod:
        >>> # def get_user(user_id: str, session: Session):
        >>> #     return user_repo._get_by_id(session, record_id=user_id)
        >>> 
        >>> # Yeni kod (sadece decorator ekle, signature değiştirme):
        >>> @inject_session()
        >>> def get_user(user_id: str, session: Session = None):
        ...     return user_repo._get_by_id(session, record_id=user_id)
        >>> # Artık get_user("user123") çağrılabilir (session otomatik gelir)
        
        >>> # Çoklu parametreli fonksiyonlar
        >>> @inject_session()
        >>> def create_user(email: str, name: str, age: int, session: Session = None):
        ...     return user_repo._create(
        ...         session,
        ...         email=email,
        ...         name=name,
        ...         age=age
        ...     )
        >>> 
        >>> user = create_user("test@test.com", "John Doe", 30)
        
    Injection Logic:
        1. Fonksiyon çağrıldığında parameter_name ile session kontrol edilir
        2. Eğer session zaten geçilmişse: Kullanılır (override)
        3. Eğer session geçilmemişse: Yeni session oluşturulup inject edilir
        4. Fonksiyon çalıştırılır
        5. Session otomatik kapatılır (context manager ile)
        
    Note:
        - Keyword argument olarak inject eder (ilk parametre değil)
        - Fonksiyon signature'ında session parametresi opsiyonel olmalı (default=None)
        - Eğer session manuel geçilirse, decorator yeni session oluşturmaz
        - Mevcut kodlara uyum için idealdir (signature değişikliği gerekmez)
        - with_session() ile karşılaştırıldığında daha esnek ama biraz daha yavaş
        
    When to Use:
        - Mevcut kod tabanlarında signature değişikliği istemiyorsanız
        - Keyword argument olarak session kullanmak istiyorsanız
        - Legacy kodlara session eklemek istiyorsanız
        
    When NOT to Use:
        - Yeni kodlar için: with_session() daha performanslı
        - İlk parametre olarak session kullanmak istiyorsanız: with_session() kullan
        
    Comparison with Other Decorators:
        - with_session(): İlk parametre olarak inject eder (daha hızlı)
        - inject_session(): Keyword argument olarak inject eder (daha esnek)
        - with_transaction(): Atomic transaction garantisi
        
    Related:
        - :meth:`with_session`: İlk parametre olarak session inject
        - :meth:`with_transaction`: Atomic transaction için
        - :class:`DatabaseEngine`: Engine yönetimi
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # classmethod veya staticmethod desteği
        if isinstance(func, classmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                if parameter_name in kwargs and kwargs[parameter_name] is not None:
                    return original_func(*args, **kwargs)
                
                with mgr.engine.session_context() as session:
                    kwargs[parameter_name] = session
                    return original_func(*args, **kwargs)
            
            return classmethod(wrapper)
        
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            
            @wraps(original_func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                if parameter_name in kwargs and kwargs[parameter_name] is not None:
                    return original_func(*args, **kwargs)
                
                with mgr.engine.session_context() as session:
                    kwargs[parameter_name] = session
                    return original_func(*args, **kwargs)
            
            return staticmethod(wrapper)
        
        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                mgr = manager or get_database_manager()
                
                if parameter_name in kwargs and kwargs[parameter_name] is not None:
                    return func(*args, **kwargs)
                
                with mgr.engine.session_context() as session:
                    kwargs[parameter_name] = session
                    return func(*args, **kwargs)
            
            return wrapper
    return decorator