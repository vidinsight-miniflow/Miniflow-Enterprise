from functools import wraps, lru_cache
from typing import Callable, TypeVar, Optional, Any, Dict
import inspect
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DBAPIError

from qbitra.core.exceptions import (
    DatabaseQueryError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorSignatureError,
)
from qbitra.database.engine.manager import DatabaseManager, get_database_manager


T = TypeVar('T')



# ============================================================================
# HELPER FUNCTIONS (DRY)
# ============================================================================

def _get_manager_or_raise(manager: Optional[DatabaseManager]) -> DatabaseManager:
    """Get manager or raise DatabaseDecoratorManagerError if not initialized (DRY helper).
    
    Args:
        manager: Optional DatabaseManager instance
        
    Returns:
        DatabaseManager: Initialized manager instance
        
    Raises:
        DatabaseDecoratorManagerError: If manager is not initialized
    """
    mgr = manager or get_database_manager()
    if mgr is None:
        raise DatabaseDecoratorManagerError(
            decorator_name="decorator",
            message="DatabaseManager not initialized. Call DatabaseManager().initialize(config) first."
        )
    return mgr




def _validate_session_signature(func: Callable, decorator_name: str) -> None:
    """Validate function has session parameter (DRY helper).
    
    This helper function centralizes signature validation logic to avoid
    code duplication across decorators.
    
    Args:
        func: Function to validate
        decorator_name: Name of the decorator (for error message)
        
    Raises:
        DatabaseDecoratorSignatureError: If function doesn't have 'session' parameter
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    if 'session' not in params:
        raise DatabaseDecoratorSignatureError(
            decorator_name=decorator_name,
            function_name=func.__name__,
            expected="session parameter",
            received=f"parameters: {params}"
        )


@lru_cache(maxsize=256)
def _get_function_signature_info(func: Callable) -> tuple:
    """Get cached function signature information.
    
    This function caches signature analysis results to improve performance.
    The cache key is based on function identity (id) and code object.
    
    Returns:
        tuple: (params_list, session_param_index, has_var_positional, has_var_keyword)
            - session_param_index: -1 if not found
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    # Find session parameter index
    try:
        session_param_index = params.index('session')
    except ValueError:
        session_param_index = -1
    
    # Check for *args and **kwargs
    has_var_positional = False
    has_var_keyword = False
    
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            has_var_positional = True
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            has_var_keyword = True
    
    return (tuple(params), session_param_index, has_var_positional, has_var_keyword)


def _create_decorator_wrapper(
    func: Callable,
    original_func: Callable,
    manager: Optional[DatabaseManager],
    context_kwargs: Dict[str, Any],
    is_classmethod: bool = False,
    is_staticmethod: bool = False,
    savepoint: bool = False
) -> Callable:
    """Create a wrapper function for decorators (DRY helper).
    
    This helper function eliminates code duplication across decorators by
    providing a common wrapper creation pattern for classmethod, staticmethod,
    and normal functions.
    
    Args:
        func: Original function (for classmethod/staticmethod, this is the wrapper)
        original_func: Actual function to call (func.__func__ for classmethod/staticmethod)
        manager: DatabaseManager instance (None to use global)
        context_kwargs: Keyword arguments for session_context()
        is_classmethod: Whether this is a classmethod decorator
        is_staticmethod: Whether this is a staticmethod decorator
        savepoint: Whether to use savepoint for nested transactions
    
    Returns:
        Wrapped function (classmethod/staticmethod wrapper or normal function)
    """
    @wraps(original_func)
    def wrapper(*args, **kwargs) -> Any:
        mgr = _get_manager_or_raise(manager)
        
        try:
            with mgr.engine.session_context(**context_kwargs) as session:
                # Handle savepoint for nested transactions (with_transaction only)
                if savepoint and session.in_transaction():
                    with session.begin_nested():
                        return _inject_session_parameter(original_func, session, args, kwargs)
                else:
                    return _inject_session_parameter(original_func, session, args, kwargs)
        except Exception as e:
            raise
    
    if is_classmethod:
        return classmethod(wrapper)
    elif is_staticmethod:
        return staticmethod(wrapper)
    else:
        return wrapper


def _inject_session_parameter(func: Callable, session: Session, args: tuple, kwargs: dict) -> Any:
    """
    Inject session parameter correctly for both functions and methods.
    
    This improved version gracefully handles user mistakes:
    - If user accidentally passes session → Override with decorator's session
    - If user correctly omits session → Insert decorator's session
    - Works with both positional args and keyword args
    - Supports *args and **kwargs
    - Optimized with caching for better performance
    
    Args:
        func: The function to call
        session: The session to inject (from decorator)
        args: Positional arguments from the original call
        kwargs: Keyword arguments from the original call
    
    Returns:
        The result of the function call
        
    Algorithm:
        1. Get cached signature information
        2. Check if session is in kwargs → override it
        3. Handle *args/**kwargs if present
        4. Count actual vs expected args and insert/override session
    """
    # Get cached signature info
    params, session_param_index, has_var_positional, has_var_keyword = _get_function_signature_info(func)
    
    # No session parameter found
    if session_param_index == -1:
        # If function doesn't have session parameter, just call as-is
        # This can happen with *args/**kwargs functions
        return func(*args, **kwargs)
    
    # CASE 1: Session passed as or should be passed as keyword argument
    if 'session' in kwargs:
        # Override the keyword argument with decorator's session
        modified_kwargs = dict(kwargs)
        modified_kwargs['session'] = session
        return func(*args, **modified_kwargs)
    
    # CASE 2: Session passed as positional argument (or position exists)
    if len(args) > session_param_index:
        args_list = list(args)
        args_list[session_param_index] = session
        return func(*args_list, **kwargs)
    
    # CASE 3: Session not passed, and position not reached - safe to inject via kwargs
    # This handles functions like foo(a, b, session=None, c=1) called as foo(1, 2, c=3)
    modified_kwargs = dict(kwargs)
    modified_kwargs['session'] = session
    return func(*args, **modified_kwargs)


def _create_retry_wrapper(
    func: Callable,
    original_func: Callable,
    manager: Optional[DatabaseManager],
    max_attempts: int,
    delay: float,
    backoff: float,
    auto_commit: bool,
    is_classmethod: bool = False,
    is_staticmethod: bool = False
) -> Callable:
    """Create retry wrapper for with_retry_session decorator (DRY helper).
    
    Args:
        func: Original function (for classmethod/staticmethod, this is the wrapper)
        original_func: Actual function to call
        manager: DatabaseManager instance (None to use global)
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        auto_commit: Whether to auto-commit
        is_classmethod: Whether this is a classmethod decorator
        is_staticmethod: Whether this is a staticmethod decorator
    
    Returns:
        Wrapped function with retry logic
    """
    @wraps(original_func)
    def wrapper(*args, **kwargs) -> Any:
        mgr = _get_manager_or_raise(manager)
        last_exception: Optional[Exception] = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                with mgr.engine.session_context(
                    auto_commit=auto_commit,
                    auto_flush=True
                ) as session:
                    result = _inject_session_parameter(original_func, session, args, kwargs)
                    
                    return result
            
            except (OperationalError, DBAPIError, DatabaseQueryError) as e:
                last_exception = e
                
                # Use improved deadlock detection from engine
                from qbitra.database.engine.engine import _is_deadlock_error
                is_deadlock = _is_deadlock_error(e)
                
                if not is_deadlock or attempt >= max_attempts:
                    raise
                
                wait_time = delay * (backoff ** (attempt - 1))
                time.sleep(wait_time)
            
            except SQLAlchemyError as e:
                raise
        
        raise last_exception or RuntimeError("Unexpected retry flow")
    
    if is_classmethod:
        return classmethod(wrapper)
    elif is_staticmethod:
        return staticmethod(wrapper)
    else:
        return wrapper


def _create_inject_wrapper(
    func: Callable,
    original_func: Callable,
    manager: Optional[DatabaseManager],
    parameter_name: str,
    is_classmethod: bool = False,
    is_staticmethod: bool = False
) -> Callable:
    """Create inject wrapper for inject_session decorator (DRY helper).
    
    Args:
        func: Original function (for classmethod/staticmethod, this is the wrapper)
        original_func: Actual function to call
        manager: DatabaseManager instance (None to use global)
        parameter_name: Name of parameter to inject session into
        is_classmethod: Whether this is a classmethod decorator
        is_staticmethod: Whether this is a staticmethod decorator
    
    Returns:
        Wrapped function with session injection
    """
    @wraps(original_func)
    def wrapper(*args, **kwargs) -> Any:
        mgr = _get_manager_or_raise(manager)
        
        try:
            if parameter_name in kwargs and kwargs[parameter_name] is not None:
                return original_func(*args, **kwargs)
            
            with mgr.engine.session_context() as session:
                kwargs[parameter_name] = session
                return original_func(*args, **kwargs)
        except Exception as e:
            raise
    
    if is_classmethod:
        return classmethod(wrapper)
    elif is_staticmethod:
        return staticmethod(wrapper)
    else:
        return wrapper


def with_session(
    auto_commit: bool = True,
    auto_flush: bool = True,
    isolation_level: Optional[str] = None,
    manager: Optional[DatabaseManager] = None,
    validate_signature: bool = True
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
        # Function signature validation
        if validate_signature:
            _validate_session_signature(func, 'with_session')
        
        # Manager validation (will be resolved in wrapper)
        # Context kwargs for session_context
        context_kwargs = {
            'auto_commit': auto_commit,
            'auto_flush': auto_flush,
            'isolation_level': isolation_level
        }
        
        # Use DRY helper to create wrapper
        if isinstance(func, classmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs, is_classmethod=True
            )
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs, is_staticmethod=True
            )
        else:
            return _create_decorator_wrapper(
                func, func, manager, context_kwargs
            )
    return decorator


def with_transaction_session(
    isolation_level: Optional[str] = None,
    savepoint: bool = False,
    manager: Optional[DatabaseManager] = None,
    validate_signature: bool = True
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
        # Function signature validation
        if validate_signature:
            _validate_session_signature(func, 'with_transaction')
        
        # Manager validation (will be resolved in wrapper)
        # Context kwargs for session_context
        context_kwargs = {
            'auto_commit': True,
            'auto_flush': True,
            'isolation_level': isolation_level
        }
        
        # Use DRY helper to create wrapper
        if isinstance(func, classmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs,
                is_classmethod=True, savepoint=savepoint
            )
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs,
                is_staticmethod=True, savepoint=savepoint
            )
        else:
            return _create_decorator_wrapper(
                func, func, manager, context_kwargs, savepoint=savepoint
            )
    return decorator


def with_readonly_session(
    manager: Optional[DatabaseManager] = None,
    validate_signature: bool = True
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
        # Function signature validation
        if validate_signature:
            _validate_session_signature(func, 'with_readonly_session')
        
        # Manager validation (will be resolved in wrapper)
        # Context kwargs for session_context (read-only)
        context_kwargs = {
            'auto_commit': False,
            'auto_flush': False,
            'isolation_level': None
        }
        
        # Use DRY helper to create wrapper
        if isinstance(func, classmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs, is_classmethod=True
            )
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            return _create_decorator_wrapper(
                func, original_func, manager, context_kwargs, is_staticmethod=True
            )
        else:
            return _create_decorator_wrapper(
                func, func, manager, context_kwargs
            )
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
    
    Args:
        max_attempts (int): Maksimum deneme sayısı.
            - Varsayılan: 3
            - Minimum: 1 (en az bir deneme)
            - Önerilen: 3-5 (deadlock durumlarında yeterli)
            - Validation: max_attempts < 1 ise ValueError fırlatılır
            
        delay (float): İlk deneme arası bekleme süresi (saniye).
            - Varsayılan: 0.1 (100ms)
            - Önerilen: 0.1-0.5 saniye
            - Validation: delay < 0 ise ValueError fırlatılır
            
        backoff (float): Her denemede bekleme süresini çarpan.
            - Varsayılan: 2.0 (her denemede 2x artar)
            - Örnek: delay=0.1, backoff=2.0 → 0.1s, 0.2s, 0.4s, 0.8s...
            - Validation: backoff <= 0 ise ValueError fırlatılır
            
        auto_commit (bool): İşlem sonunda otomatik commit yapılsın mı?
            - True (varsayılan): Başarılı olursa otomatik commit
            - False: Manuel commit gerekir
            
        manager (Optional[DatabaseManager]): Kullanılacak DatabaseManager.
            - None (varsayılan): Global singleton manager
            
    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: Dekore edilmiş fonksiyon
        
    Raises:
        ValueError: Parameter validation hatası
            - max_attempts < 1
            - delay < 0
            - backoff <= 0
        RuntimeError: DatabaseManager initialize edilmemişse
        DatabaseConnectionError: Veritabanı bağlantı hatası (retry edilemez)
        DatabaseQueryError: Deadlock/timeout hatası (retry edilir)
        DatabaseError: Diğer veritabanı hataları
    """
    # Parameter validation
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError(f"max_attempts must be a positive integer, got {max_attempts}")
    
    if not isinstance(delay, (int, float)) or delay < 0:
        raise ValueError(f"delay must be a non-negative number, got {delay}")
    
    if not isinstance(backoff, (int, float)) or backoff <= 0:
        raise ValueError(f"backoff must be a positive number, got {backoff}")
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Use DRY helper for retry wrapper
        if isinstance(func, classmethod):
            original_func = func.__func__
            return _create_retry_wrapper(
                func, original_func, manager, max_attempts, delay, backoff, auto_commit,
                is_classmethod=True
            )
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            return _create_retry_wrapper(
                func, original_func, manager, max_attempts, delay, backoff, auto_commit,
                is_staticmethod=True
            )
        else:
            return _create_retry_wrapper(
                func, func, manager, max_attempts, delay, backoff, auto_commit
            )
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
        # Use DRY helper for inject wrapper
        if isinstance(func, classmethod):
            original_func = func.__func__
            return _create_inject_wrapper(
                func, original_func, manager, parameter_name, is_classmethod=True
            )
        elif isinstance(func, staticmethod):
            original_func = func.__func__
            return _create_inject_wrapper(
                func, original_func, manager, parameter_name, is_staticmethod=True
            )
        else:
            return _create_inject_wrapper(
                func, func, manager, parameter_name
            )
    return decorator