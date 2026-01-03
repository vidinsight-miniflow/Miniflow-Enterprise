import time
import weakref
import threading
from functools import wraps
from contextlib import contextmanager
from typing import Optional, Callable, TypeVar, Tuple, Type, Set

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DBAPIError

from ..config import DatabaseConfig
from miniflow.core.exceptions import (
    DatabaseError, DatabaseConnectionError, DatabaseQueryError,
    DatabaseConfigurationError, DatabaseSessionError, DatabaseEngineError,
    DatabaseTransactionError
)
from miniflow.core.logger import get_logger, log_function_call

# Logger instance
logger = get_logger(__name__)

# Type variable for generic return types
T = TypeVar('T')


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _is_deadlock_error(error: Exception) -> bool:
    """Deadlock veya kilit zaman aşımı hatası tespiti.
    
    Bu utility fonksiyonu, bir exception'un deadlock veya lock timeout
    hatası olup olmadığını kontrol eder. Retry mekanizmaları için
    kullanılır.
    
    Args:
        error (Exception): Kontrol edilecek exception instance'ı
        
    Returns:
        bool: Deadlock/timeout hatası ise True, değilse False
        
    Tespit Edilen Hatalar:
        - "deadlock" kelimesi içeren hatalar
        - "lock timeout" içeren hatalar
        - "lock wait timeout" içeren hatalar
        - "could not obtain lock" içeren hatalar
        - MySQL error code: 1213 (deadlock)
        - PostgreSQL error code: 40p01 (deadlock)
        - Oracle error code: ora-00060 (deadlock)
        
    Examples:
        >>> try:
        ...     # Veritabanı işlemi
        ...     pass
        ... except OperationalError as e:
        ...     if _is_deadlock_error(e):
        ...         # Retry yapılabilir
        ...         retry_operation()
        
    Note:
        - Case-insensitive string matching kullanır
        - Database-agnostic: Tüm major database'leri destekler
        - Internal utility function: Dışarıdan kullanım için tasarlanmamış
    """
    error_msg = str(error).lower()
    deadlock_indicators = [
        'deadlock', 
        'lock timeout', 
        'lock wait timeout', 
        'could not obtain lock',
        '1213',      # MySQL deadlock
        '40p01',     # PostgreSQL deadlock
        'ora-00060'  # Oracle deadlock
    ]
    return any(indicator in error_msg for indicator in deadlock_indicators)


def with_retry(
    max_attempts: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (OperationalError, DBAPIError),
    retry_on_deadlock_only: bool = True
):
    """Akıllı yeniden deneme mantığıyla veritabanı işlemleri için decorator.
    
    Bu decorator, deadlock ve timeout hatalarında otomatik retry yapar.
    Exponential backoff stratejisi kullanarak her denemede bekleme süresini
    artırır. Veritabanı işlemleri için kullanılabilir ancak session yönetimi
    yapmaz (with_retry_session() tercih edilmeli).
    
    Args:
        max_attempts (int): Maksimum deneme sayısı. Varsayılan: 3
        delay (float): İlk deneme arası bekleme süresi (saniye). Varsayılan: 0.1
        backoff (float): Her denemede bekleme süresini çarpan. Varsayılan: 2.0
        retry_exceptions (Tuple[Type[Exception], ...]): Retry yapılacak exception tipleri.
            Varsayılan: (OperationalError, DBAPIError)
        retry_on_deadlock_only (bool): Sadece deadlock hatalarında retry yap.
            Varsayılan: True
            
    Returns:
        Callable: Dekore edilmiş fonksiyon
        
    Examples:
        >>> @with_retry(max_attempts=3)
        >>> def database_operation():
        ...     # Deadlock olursa otomatik retry
        ...     pass
        
    Note:
        - Session yönetimi yapmaz (with_retry_session() kullanın)
        - Deadlock detection için _is_deadlock_error() kullanır
        - Exponential backoff: delay * (backoff ^ attempt)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt}/{max_attempts}")
                    return result
                    
                except retry_exceptions as e:
                    last_exception = e
                    is_deadlock = _is_deadlock_error(e)
                    
                    # Yeniden deneme kararı
                    should_retry = is_deadlock if retry_on_deadlock_only else True
                    
                    # Son denemede direkt raise et (unreachable code önleme)
                    if attempt >= max_attempts:
                        error_type = "deadlock" if is_deadlock else "database error"
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}", exc_info=True)
                        raise
                    
                    # Retry yapılamayacak hata
                    if not should_retry:
                        logger.error(f"{func.__name__} failed with non-deadlock error: {e}", exc_info=True)
                        raise
                    
                    # Yeniden denemeden önce bekleme
                    wait_time = delay * (backoff ** (attempt - 1))
                    error_type = "deadlock" if is_deadlock else "database error"
                    
                    logger.warning(f"{func.__name__} {error_type} on attempt {attempt}, "
                          f"retrying in {wait_time:.2f}s: {e}")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error(f"{func.__name__} failed with non-retryable error: {e}", exc_info=True)
                    raise
            
            # Bu satıra asla ulaşılmamalı (safety net)
            raise RuntimeError(f"Unexpected retry flow for {func.__name__}")
                
        return wrapper
    return decorator


# ============================================================================
# DATABASE ENGINE
# ============================================================================

class DatabaseEngine:
    """Üretim hazır veritabanı motoru - bağlantı havuzu ve oturum yönetimi.
    
    Bu sınıf, SQLAlchemy engine'i ve session factory'yi yönetir, bağlantı havuzu
    oluşturur ve thread-safe session yönetimi sağlar. Production-ready bir
    veritabanı katmanı sunar.
    
    Özellikler:
        - Connection Pooling: Verimli bağlantı yönetimi
        - Thread-Safe: Multi-threaded ortamlarda güvenli kullanım
        - Session Tracking: Aktif session'ları takip eder
        - Context Manager: Güvenli session yaşam döngüsü
        - Health Check: Veritabanı durumunu kontrol eder
        - Resource Cleanup: Graceful shutdown
    
    Yaşam Döngüsü:
        1. __init__(config): Engine'i başlatır (henüz bağlanmaz)
        2. start(): Engine'i başlatır ve bağlantı havuzunu oluşturur
        3. session_context(): Session oluşturur ve yönetir
        4. stop(): Tüm kaynakları temizler ve engine'i kapatır
    
    Thread Safety:
        - Tüm session tracking operasyonları thread-safe (RLock kullanır)
        - Her thread kendi session'ını alır
        - Connection pool thread-safe (SQLAlchemy garantisi)
        - Weak reference tracking thread-safe
    
    Examples:
        >>> # Engine oluşturma ve başlatma
        >>> config = DatabaseConfig(
        ...     db_type=DatabaseType.POSTGRESQL,
        ...     db_name="mydb",
        ...     host="localhost",
        ...     port=5432,
        ...     username="user",
        ...     password="pass"
        ... )
        >>> engine = DatabaseEngine(config)
        >>> engine.start()
        
        >>> # Context manager ile session kullanımı
        >>> with engine.session_context() as session:
        ...     user = user_repo._get_by_id(session, record_id="user123")
        ...     # Otomatik commit ve session kapatma
        
        >>> # Manuel session yönetimi
        >>> session = engine.get_session()
        >>> try:
        ...     user = user_repo._create(session, email="test@test.com")
        ...     session.commit()
        ... finally:
        ...     session.close()
        
        >>> # Health check
        >>> health = engine.health_check()
        >>> print(health['status'])  # 'healthy', 'unhealthy', 'stopped'
        
        >>> # Graceful shutdown
        >>> engine.stop()  # Tüm session'ları kapatır ve kaynakları temizler
    
    Note:
        - Engine başlatılmadan session kullanılamaz (start() çağrılmalı)
        - Context manager (session_context) kullanımı önerilir
        - stop() çağrıldığında tüm aktif session'lar kapatılır
        - Thread-safe: Multi-threaded uygulamalarda güvenle kullanılabilir
        
    Related:
        - :class:`DatabaseManager`: Singleton pattern ile engine yönetimi
        - :class:`DatabaseConfig`: Konfigürasyon yönetimi
        - :meth:`session_context`: Güvenli session context manager
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """DatabaseEngine'i veritabanı konfigürasyonu ile başlatır.
        
        Bu constructor, engine'i oluşturur ancak henüz veritabanına bağlanmaz.
        Bağlantı ve engine oluşturma start() metodu çağrıldığında yapılır.
        
        Args:
            config (DatabaseConfig): Veritabanı konfigürasyonu.
                - db_type: Veritabanı tipi (PostgreSQL, MySQL, SQLite vb.)
                - db_name: Veritabanı adı
                - host, port, username, password: Bağlantı bilgileri
                - engine_config: Engine konfigürasyonu (pool size, timeout vb.)
                
        Raises:
            DatabaseConfigurationError: Konfigürasyon geçersiz ise
                - config None veya boş ise
                - db_name boş ise
                - pool_size <= 0 ise
                
        Examples:
            >>> # PostgreSQL konfigürasyonu
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.POSTGRESQL,
            ...     db_name="production_db",
            ...     host="db.example.com",
            ...     port=5432,
            ...     username="app_user",
            ...     password="secure_password"
            ... )
            >>> engine = DatabaseEngine(config)
            >>> # Engine oluşturuldu ama henüz başlatılmadı
            
            >>> # SQLite konfigürasyonu (geliştirme)
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name="dev.db"
            ... )
            >>> engine = DatabaseEngine(config)
        
        Note:
            - Engine başlatılmadan session kullanılamaz
            - start() metodunu çağırmadan önce engine hazır değildir
            - Konfigürasyon doğrulaması yapılır (validation)
            - Thread-safe initialization (her thread kendi engine instance'ı alabilir)
        """
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.config = self._validate_config(config)
        
        # Get and validate connection string
        connection_string = config.get_connection_string()
        
        # GARANTİLİ STRING'E ÇEVİRME (ekstra güvenlik katmanı)
        # Eğer bir şekilde integer veya başka bir tip gelirse, string'e çevir
        if not isinstance(connection_string, str):
            # Önce string'e çevirmeyi dene (defensive programming)
            try:
                connection_string = str(connection_string) if connection_string is not None else ""
            except Exception as e:
                # String'e çevrilemezse hata ver
                error_details = {
                    "expected_type": "str",
                    "actual_type": type(connection_string).__name__,
                    "actual_value": repr(connection_string),
                    "conversion_error": str(e),
                    "config.db_type": config.db_type.value if hasattr(config, 'db_type') else "unknown",
                    "config.db_name": getattr(config, 'db_name', "unknown"),
                    "config.host": getattr(config, 'host', "unknown"),
                    "config.port": getattr(config, 'port', "unknown"),
                    "config.sqlite_path": getattr(config, 'sqlite_path', "unknown"),
                }
                logger.critical(f"DatabaseEngine.__init__: Connection string validation FAILED! Details: {error_details}")
                error = DatabaseConfigurationError(
                    config_name={"connection_string_validation_failed": error_details}
                )
                self._log_error("__init__", error)
                raise error
        
        # Boş string kontrolü
        if not connection_string:
            error_msg = (
                f"[DatabaseEngine.__init__] CRITICAL: Empty connection string!\n"
                f"  Location: engine.py, line ~319\n"
                f"  Method: __init__()\n"
                f"  Expected: Non-empty connection string\n"
                f"  Received: Empty string ''\n"
                f"  Database Configuration:\n"
                f"    - db_type: {config.db_type.value if hasattr(config, 'db_type') else 'unknown'}\n"
                f"    - db_name: {getattr(config, 'db_name', 'unknown')}\n"
                f"    - host: {getattr(config, 'host', 'unknown')}\n"
                f"    - port: {getattr(config, 'port', 'unknown')}\n"
                f"  Reason: config.get_connection_string() returned empty string\n"
                f"  This indicates a configuration error.\n"
                f"  Solution: Check your DatabaseConfig parameters\n"
                f"  Example: DatabaseConfig(db_type=DatabaseType.POSTGRESQL, host='localhost', port=5432, db_name='mydb', username='user', password='pass')"
            )
            logger.critical(error_msg)
            raise DatabaseConfigurationError(
                config_name={
                    "error": "Connection string is empty",
                    "details": error_msg
                }
            )
        
        self._connection_string: str = connection_string
        self._base_metadata = None
        
        # Thread-safe oturum takibi
        self._active_sessions: Set[weakref.ref] = set()
        self._session_lock = threading.RLock()
        self._shutdown = False  # Shutdown flag for race condition prevention
        
        logger.info(f"DatabaseEngine initialized for: {config.db_name}")

    def _log_error(self, operation: str, error: Exception):
        """Hata durumlarını tutarlı şekilde loglamak için yardımcı."""
        logger.error(f"DatabaseEngine.{operation}: {error}", exc_info=True)

    def _validate_config(self, config: DatabaseConfig) -> DatabaseConfig:
        """Veritabanı konfigürasyonunu doğrula."""
        if not config or not config.db_name:
            error = DatabaseConfigurationError(config_name={"config": str(config), "db_name": config.db_name if config else None})
            self._log_error("validate_config", error)
            raise error

        # Pool boyutunu kontrol et
        if (config.engine_config and 
            getattr(config.engine_config, 'pool_size', 1) <= 0):
            error = DatabaseConfigurationError(config_name={"pool_size": getattr(config.engine_config, 'pool_size', None)})
            self._log_error("validate_config", error)
            raise error

        return config
    
    def _build_engine(self) -> None:
        """Bağlantı havuzu ile SQLAlchemy engine oluştur."""
        try:
            engine_kwargs = self.config.engine_config.to_engine_kwargs()
            # DatabaseConfig seviyesindeki connect_args'ı kullan (DB-özgü varsayılanlar + override)
            engine_kwargs['connect_args'] = self.config.get_connect_args()
            # Seçilen veritabanı tipine uygun pool sınıfını seç
            pool_class = self.config.get_pool_class()
            engine_kwargs['poolclass'] = pool_class
            
            # NullPool ve StaticPool pool_size, max_overflow, pool_timeout, pool_recycle desteklemez
            # Bu parametreleri bu pool sınıfları için kaldır
            from sqlalchemy.pool import NullPool, StaticPool
            if pool_class in (NullPool, StaticPool):
                engine_kwargs.pop('pool_size', None)
                engine_kwargs.pop('max_overflow', None)
                engine_kwargs.pop('pool_timeout', None)
                engine_kwargs.pop('pool_recycle', None)
                engine_kwargs.pop('pool_pre_ping', None)

            self._engine = create_engine(self._connection_string, **engine_kwargs)
            logger.info("Database engine created successfully")

        except Exception as e:
            error = DatabaseEngineError()
            self._log_error("build_engine", error)
            raise error
        
    def _build_session_factory(self) -> None:
        """Veritabanı oturumları oluşturmak için session factory oluştur."""
        try:
            session_kwargs = self.config.engine_config.to_session_kwargs()
            session_kwargs['bind'] = self._engine
            # Isolation level kaldırıldı - session_context'te uygulanacak
            
            self._session_factory = sessionmaker(**session_kwargs)
            logger.info("Session factory created successfully")

        except Exception as e:
            error = DatabaseSessionError()
            self._log_error("build_session_factory", error)
            raise error
        
    def _cleanup_resources(self) -> None:
        """Tüm veritabanı kaynaklarını temizle."""
        # Shutdown flag'ini set et (race condition önleme)
        self._shutdown = True
        
        cleanup_errors = []
        
        # Takip edilen aktif oturumları kapat
        with self._session_lock:
            active_count = 0
            for session_ref in list(self._active_sessions):
                session = session_ref()
                if session is not None:
                    try:
                        if session.is_active:
                            session.rollback()
                        session.close()
                        active_count += 1
                    except Exception as e:
                        cleanup_errors.append(f"Failed to close session: {e}")
            
            if active_count > 0:
                logger.warning(f"Closed {active_count} active sessions during cleanup")
            
            self._active_sessions.clear()
        
        # Engine ve bağlantı havuzunu dispose et
        if self._engine is not None:
            try:
                self._engine.dispose()
            except Exception as e:
                cleanup_errors.append(f"Failed to dispose engine: {e}")
        
        # Referansları temizle
        self._engine = None
        self._session_factory = None
        
        # Shutdown flag'ini reset et (tekrar başlatma için)
        self._shutdown = False
        
        # Temizlik hatalarını logla
        if cleanup_errors:
            logger.error(f"Cleanup errors: {'; '.join(cleanup_errors)}")
    
    def _track_session(self, session: Session) -> None:
        """Temizlik için weak reference kullanarak oturumu takip et."""
        def cleanup_callback(ref):
            # Shutdown flag kontrolü ile race condition önleme
            if not self._shutdown:
                try:
                    with self._session_lock:
                        self._active_sessions.discard(ref)
                except:
                    # Lock silinmiş olabilir (shutdown sırasında)
                    pass
        
        with self._session_lock:
            session_ref = weakref.ref(session, cleanup_callback)
            self._active_sessions.add(session_ref)
            # Session objesi üzerinde referansı sakla (untrack için)
            session._miniflow_ref = session_ref
    
    def _untrack_session(self, session: Session) -> None:
        """Session'ı aktif listeden çıkar.
        
        session.close() çağrıldıktan sonra weak reference listesinden
        manuel olarak çıkarmak için kullanılır. Garbage collection
        beklemeden session'ın pasif olduğunu işaretler.
        
        Args:
            session: Çıkarılacak session
        """
        try:
            with self._session_lock:
                # Session'a kaydedilmiş referansı bul
                if hasattr(session, '_miniflow_ref'):
                    self._active_sessions.discard(session._miniflow_ref)
                    delattr(session, '_miniflow_ref')
        except Exception as e:
            # Session zaten GC olmuş veya lock silinmiş olabilir
            pass
    
    def get_active_session_count(self) -> int:
        """Şu anda aktif olan oturum sayısını döndürür.
        
        Bu metod, weak reference tracking kullanarak aktif session sayısını
        döndürür. Ölü referansları (garbage collected) otomatik temizler.
        
        Returns:
            int: Aktif session sayısı
                - 0: Hiç aktif session yok
                - N: N adet aktif session var
                - Ölü referanslar otomatik temizlenir
                
        Examples:
            >>> # Aktif session sayısını kontrol et
            >>> count = engine.get_active_session_count()
            >>> print(f"Aktif session sayısı: {count}")
            
            >>> # Health check için
            >>> health = engine.health_check()
            >>> active_sessions = health['active_sessions']  # Bu metod kullanılır
        
        Note:
            - Weak reference tracking kullanır
            - Ölü referansları otomatik temizler
            - Thread-safe: RLock kullanır
            - Engine başlatılmamışsa 0 döner
            - Performance: O(n) complexity (n = tracked sessions)
            
        Related:
            - :meth:`_track_session`: Session takibi için
            - :meth:`health_check`: Health check'te kullanılır
            - :meth:`close_all_sessions`: Tüm session'ları kapatır
        """
        if not hasattr(self, '_active_sessions'):
            return 0
        
        with self._session_lock:
            # Ölü referansları temizle ve sayıyı döndür
            self._active_sessions = {
                ref for ref in self._active_sessions if ref() is not None
            }
            return len(self._active_sessions)

    @log_function_call
    def start(self) -> None:
        """Veritabanı motorunu başlatır ve bağlantı havuzunu oluşturur.
        
        Bu metod, SQLAlchemy engine'ini ve session factory'yi oluşturur.
        Veritabanına bağlantı kurulur ve connection pool hazır hale getirilir.
        Engine başlatılmadan session oluşturulamaz.
        
        Çalışma Mantığı:
            1. Engine zaten başlatılmışsa uyarı verir ve çıkar
            2. SQLAlchemy engine oluşturulur (_build_engine)
            3. Session factory oluşturulur (_build_session_factory)
            4. Engine artık kullanıma hazırdır
        
        Raises:
            DatabaseEngineError: Engine oluşturulurken hata varsa
            DatabaseSessionError: Session factory oluşturulurken hata varsa
            DatabaseConnectionError: Veritabanı bağlantı hatası varsa
            
        Examples:
            >>> # Engine başlatma
            >>> engine = DatabaseEngine(config)
            >>> engine.start()  # Bağlantı havuzu oluşturulur
            >>> # Artık session kullanılabilir
            
            >>> # Tekrar başlatma (uyarı verir)
            >>> engine.start()  # "[WARNING] Database engine already started"
            
            >>> # Context manager ile kullanım
            >>> engine.start()
            >>> with engine.session_context() as session:
            ...     # İşlemler
            ...     pass
        
        Note:
            - İkinci kez çağrılırsa uyarı verir (idempotent)
            - Engine başlatılmadan session_context() kullanılamaz
            - stop() çağrıldıktan sonra tekrar start() çağrılabilir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            
        Related:
            - :meth:`stop`: Engine'i durdurur
            - :meth:`is_alive`: Engine durumunu kontrol eder
            - :meth:`session_context`: Session oluşturur
        """
        if self._engine is not None:
            logger.warning("Database engine already started")
            return
            
        logger.info("Starting database engine...")
        self._build_engine()
        self._build_session_factory()
        logger.info("Database engine started successfully")

    def stop(self) -> None:
        """Veritabanı motorunu durdurur ve tüm kaynakları temizler.
        
        Bu metod, engine'i güvenli bir şekilde kapatır:
        1. Tüm aktif session'ları rollback eder ve kapatır
        2. Connection pool'u dispose eder
        3. Engine referanslarını temizler
        4. Kaynakları serbest bırakır
        
        Graceful Shutdown:
            - Aktif transaction'lar rollback edilir
            - Session'lar güvenli şekilde kapatılır
            - Connection pool temizlenir
            - Memory leak'leri önlenir
        
        Args:
            Yok (parametresiz metod)
            
        Raises:
            Exception: Cleanup sırasında hata olursa (loglanır ama fırlatılmaz)
            
        Examples:
            >>> # Normal kullanım
            >>> engine.start()
            >>> # ... işlemler ...
            >>> engine.stop()  # Graceful shutdown
            
            >>> # Context manager ile
            >>> engine.start()
            >>> try:
            ...     with engine.session_context() as session:
            ...         # İşlemler
            ...         pass
            ... finally:
            ...     engine.stop()  # Her durumda temizlik
            
            >>> # Aktif session'larla kapanma
            >>> engine.start()
            >>> session1 = engine.get_session()
            >>> session2 = engine.get_session()
            >>> engine.stop()  # Her iki session da kapatılır
        
        Warning:
            ⚠️ Aktif session'lar varsa uyarı verilir ancak yine de kapatılır.
            ⚠️ Stop edilmiş engine'de session oluşturulamaz (start() gerekir).
            ⚠️ Uzun süren transaction'lar rollback edilir (data loss riski).
        
        Note:
            - İkinci kez çağrılırsa sessizce geçer (idempotent)
            - stop() sonrası tekrar start() çağrılabilir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            - Application shutdown'da mutlaka çağrılmalı
            
        Related:
            - :meth:`start`: Engine'i başlatır
            - :meth:`_cleanup_resources`: Kaynak temizleme implementasyonu
        """
        if self._engine:
            logger.info("Stopping database engine...")
            active_sessions = self.get_active_session_count()
            if active_sessions > 0:
                logger.warning(f"Stopping with {active_sessions} active sessions")
            
            self._cleanup_resources()
            logger.info("Database engine stopped successfully")
    
    def create_tables(self, base_metadata) -> None:
        """Veritabanı tablolarını oluşturur.
        
        Bu metod, SQLAlchemy Base.metadata kullanarak tüm tanımlı tabloları
        veritabanında oluşturur. Migration tool'ları yerine kullanılabilir
        veya development/test ortamlarında hızlı setup için idealdir.
        
        Args:
            base_metadata: SQLAlchemy Base.metadata nesnesi.
                - Örnek: Base.metadata (SQLAlchemy declarative base'den)
                - Tüm model tanımlarını içerir
                
        Raises:
            DatabaseEngineError: Engine başlatılmamışsa
                - Error message: "Engine not initialized. Call start() first."
            DatabaseEngineError: Tablo oluşturma hatası varsa
                - Örnek: Syntax error, permission denied, table already exists vb.
                
        Examples:
            >>> # Tabloları oluştur
            >>> from database.models import Base
            >>> engine.start()
            >>> engine.create_tables(Base.metadata)
            >>> # Tüm tablolar oluşturuldu
            
            >>> # Development ortamında kullanım
            >>> def setup_database():
            ...     engine.start()
            ...     engine.create_tables(Base.metadata)
            ...     print("Database tables created")
            
            >>> # Hata durumu
            >>> try:
            ...     engine.create_tables(Base.metadata)
            ... except DatabaseEngineError as e:
            ...     print(f"Table creation failed: {e}")
        
        Warning:
            ⚠️ Production'da migration tool'ları kullanın (Alembic vb.)
            ⚠️ Mevcut tablolar varsa hata verebilir (drop_tables() önce kullanın)
            ⚠️ Foreign key constraint'ler sırası önemli olabilir
        
        Note:
            - Engine başlatılmış olmalı (start() çağrılmış olmalı)
            - SQLAlchemy create_all() metodunu kullanır
            - Mevcut tabloları yeniden oluşturmaz (if_not_exists davranışı)
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            
        Related:
            - :meth:`drop_tables`: Tabloları siler
            - :meth:`start`: Engine'i başlatır
            - :meth:`is_alive`: Engine durumunu kontrol eder
        """
        if not self.is_alive:
            error = DatabaseEngineError()
            self._log_error("create_tables", error)
            raise error
        
        try:
            logger.info("Creating database tables...")
            base_metadata.create_all(self._engine)
            self._base_metadata = base_metadata
            logger.info("Database tables created successfully")
        except Exception as e:
            error = DatabaseEngineError()
            self._log_error("create_tables", error)
            raise error
    
    def drop_tables(self, base_metadata = None) -> None:
        """Veritabanı tablolarını siler.
        
        Bu metod, SQLAlchemy Base.metadata kullanarak tüm tanımlı tabloları
        veritabanından siler. TÜM VERİLER KALICI OLARAK SİLİNİR!
        
        ⚠️ DİKKAT: Bu işlem GERİ ALINAMAZ! Tüm veriler kaybolur!
        
        Args:
            base_metadata: SQLAlchemy Base.metadata nesnesi.
                - Örnek: Base.metadata (SQLAlchemy declarative base'den)
                - Tüm model tanımlarını içerir
                
        Raises:
            DatabaseEngineError: Engine başlatılmamışsa
                - Error message: "Engine not initialized. Call start() first."
            DatabaseEngineError: Tablo silme hatası varsa
                - Örnek: Permission denied, foreign key constraint vb.
                
        Examples:
            >>> # Tüm tabloları sil (DİKKATLİ!)
            >>> from database.models import Base
            >>> engine.start()
            >>> engine.drop_tables(Base.metadata)
            >>> # ⚠️ TÜM VERİLER SİLİNDİ!
            
            >>> # Test ortamında reset
            >>> def reset_test_database():
            ...     engine.start()
            ...     engine.drop_tables(Base.metadata)  # Önce sil
            ...     engine.create_tables(Base.metadata)  # Sonra oluştur
            ...     print("Test database reset")
            
            >>> # Production'da ASLA kullanmayın!
            >>> # if environment == 'production':
            >>> #     raise RuntimeError("Drop tables not allowed in production!")
        
        Warning:
            ⚠️⚠️⚠️ KRİTİK UYARI ⚠️⚠️⚠️
            - Bu işlem TÜM VERİLERİ SİLER (GERİ ALINAMAZ!)
            - Production ortamında ASLA kullanmayın!
            - Sadece development/test ortamlarında kullanın
            - Backup alınmadan kullanmayın
            - Foreign key constraint'ler nedeniyle sıralama önemli olabilir
        
        Note:
            - Engine başlatılmış olmalı (start() çağrılmış olmalı)
            - SQLAlchemy drop_all() metodunu kullanır
            - Cascade drop davranışı database'e göre değişir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            - Migration tool'ları ile birlikte kullanmayın
            
        When to Use:
            - Test ortamında database reset
            - Development ortamında schema değişiklikleri
            - CI/CD pipeline'larında clean database setup
            
        When NOT to Use:
            - Production ortamı (ASLA!)
            - Production-like staging ortamları
            - Önemli veri içeren herhangi bir ortam
            
        Related:
            - :meth:`create_tables`: Tabloları oluşturur
            - :meth:`start`: Engine'i başlatır
            - Migration tools (Alembic): Production için önerilen yöntem
        """
        if not self.is_alive:
            error = DatabaseEngineError()
            self._log_error("drop_tables", error)
            raise error
        
        try:
            logger.warning("Dropping all database tables...")
            if not base_metadata:
                self._base_metadata.drop_all(self._engine)
            else:
                base_metadata.drop_all(self._engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            error = DatabaseEngineError()
            self._log_error("drop_tables", error)
            raise error

    @property
    def is_alive(self) -> bool:
        """Veritabanı motorunun başlatılıp hazır olup olmadığını kontrol eder.
        
        Bu property, engine'in başlatılıp başlatılmadığını kontrol eder.
        Engine başlatılmadan session oluşturulamaz.
        
        Returns:
            bool: Engine durumu
                - True: Engine başlatılmış ve hazır
                - False: Engine henüz başlatılmamış veya stop() edilmiş
                
        Examples:
            >>> # Engine durumu kontrolü
            >>> engine = DatabaseEngine(config)
            >>> print(engine.is_alive)  # False (henüz başlatılmadı)
            
            >>> engine.start()
            >>> print(engine.is_alive)  # True (başlatıldı)
            
            >>> engine.stop()
            >>> print(engine.is_alive)  # False (durdu)
            
            >>> # Session oluşturmadan önce kontrol
            >>> if engine.is_alive:
            ...     session = engine.get_session()
            ... else:
            ...     raise RuntimeError("Engine not started")
            
            >>> # Health check için
            >>> health = engine.health_check()
            >>> if not health['engine_alive']:  # is_alive property kullanılır
            ...     print("Engine is not running")
        
        Note:
            - Internal state kontrolü: _engine is not None
            - Bağlantı durumunu kontrol etmez, sadece engine varlığını
            - Detaylı durum için health_check() kullanın
            - Thread-safe: Property access thread-safe
            
        Related:
            - :meth:`start`: Engine'i başlatır
            - :meth:`stop`: Engine'i durdurur
            - :meth:`health_check`: Detaylı durum kontrolü
        """
        return self._engine is not None

    def get_session(self) -> Session:
        """Yeni bir veritabanı oturumu oluşturur ve döndürür.
        
        Bu metod, session factory kullanarak yeni bir SQLAlchemy Session
        oluşturur ve döndürür. Session tracking'e eklenir ve manuel
        yönetim gerektirir (session.close() çağrılmalı).
        
        ⚠️ DİKKAT: Context manager (session_context) kullanımı önerilir!
        
        Returns:
            Session: Yeni oluşturulmuş SQLAlchemy Session instance'ı
                - Session tracking'e eklenir
                - Çağıran taraf kapatmakla sorumludur
                - Transaction yönetimi manuel olmalı
                
        Raises:
            DatabaseEngineError: Engine başlatılmamışsa
                - Error message: "Engine not initialized. Call start() first."
            DatabaseSessionError: Session oluşturulurken hata varsa
                - Örnek: Connection pool exhausted, connection error vb.
                
        Examples:
            >>> # Manuel session yönetimi (önerilmez)
            >>> engine.start()
            >>> session = engine.get_session()
            >>> try:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     session.commit()
            ... finally:
            ...     session.close()  # Manuel kapatma gerekli
            
            >>> # Context manager kullanımı (önerilen)
            >>> with engine.session_context() as session:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     # Otomatik commit ve kapatma
            
            >>> # Birden fazla session (dikkatli kullanın)
            >>> session1 = engine.get_session()
            >>> session2 = engine.get_session()
            >>> # Her ikisini de kapatmayı unutmayın!
        
        Warning:
            ⚠️ Manuel session yönetimi hataya açıktır!
            - session.close() unutulabilir (memory leak)
            - Exception durumunda session açık kalabilir
            - Context manager (session_context) kullanımı önerilir
            - Decorator'lar (@with_session) kullanımı önerilir
            
        Note:
            - Session tracking'e otomatik eklenir (_track_session)
            - Manuel transaction yönetimi gerekir (commit/rollback)
            - Session kapatılmazsa connection pool exhausted olabilir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            - Her thread kendi session'ını alır
            
        Best Practices:
            - Context manager kullanın: with engine.session_context()
            - Decorator kullanın: @with_session()
            - Manuel kullanım gerekiyorsa try-finally kullanın
            - Her session'ı mutlaka kapatın
            
        Related:
            - :meth:`session_context`: Context manager versiyonu (önerilen)
            - :meth:`with_session`: Decorator versiyonu (önerilen)
            - :meth:`_track_session`: Session tracking implementasyonu
        """
        if not self.is_alive:
            error = DatabaseEngineError()
            self._log_error("get_session", error)
            raise error

        try:
            session = self._session_factory()
            self._track_session(session)
            
            # Wrap session.close() to auto-untrack
            original_close = session.close
            engine_ref = self  # Capture engine reference
            
            def tracked_close():
                """Wrapped close that untrucks session before closing."""
                try:
                    # Untrack before close (while session is still accessible)
                    engine_ref._untrack_session(session)
                finally:
                    # Always call original close
                    original_close()
            
            # Replace close method with tracked version
            session.close = tracked_close
            
            return session
        
        except Exception as e:
            error = DatabaseSessionError()
            self._log_error("get_session", error)
            raise error

    @contextmanager
    @log_function_call
    def session_context(
        self,
        *,
        auto_commit: bool = True,
        auto_flush: bool = True,
        isolation_level: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """Güvenli veritabanı oturum yönetimi için context manager.
        
        Bu context manager, session yaşam döngüsünü otomatik yönetir:
        - Session oluşturulur
        - İşlemler yapılır
        - Başarılı ise commit/flush
        - Hata varsa rollback
        - Her durumda session kapatılır
        
        Context Manager Mantığı:
            1. __enter__: Session oluşturulur ve yield edilir
            2. İşlemler: Fonksiyon body'si çalışır
            3. __exit__ (başarılı):
               a. auto_flush=True ve dirty varsa: flush()
               b. auto_commit=True ise: commit()
            4. __exit__ (hata):
               a. Rollback yapılır
               b. Exception yeniden fırlatılır
        
        Args:
            auto_commit (bool): İşlem sonunda otomatik commit yapılsın mı?
                - True (varsayılan): Başarılı olursa otomatik commit
                - False: Manuel commit gerekir (dikkatli kullanılmalı)
                
            auto_flush (bool): Değişiklikler otomatik flush edilsin mi?
                - True (varsayılan): Değişiklikler veritabanına gönderilir
                - False: Sadece commit edilince gönderilir
                
            isolation_level (Optional[str]): Transaction isolation seviyesi.
                - None (varsayılan): Database default isolation level
                - 'READ_COMMITTED': Yaygın kullanım (PostgreSQL default)
                - 'SERIALIZABLE': En yüksek seviye (tam izolasyon)
                - Diğer: 'READ_UNCOMMITTED', 'REPEATABLE_READ'
                
            timeout (Optional[float]): Query timeout süresi (saniye).
                - None (varsayılan): Timeout yok
                - Float/Int: Saniye cinsinden timeout (örn: 30.0 = 30 saniye)
                - Uzun sorguları otomatik iptal eder
                - PostgreSQL: statement_timeout (ms'e çevrilir)
                - MySQL: max_execution_time (ms'e çevrilir)
                - Değer aralığı: 0 < timeout <= 3600 (1 saat maksimum)
                - Geçersiz değerler için ValueError fırlatılır
        
        Yields:
            Session: SQLAlchemy session instance'ı
                - Context manager içinde kullanılır
                - Otomatik kapatılır (finally bloğu)
                
        Raises:
            DatabaseEngineError: Engine başlatılmamışsa
            ValueError: Timeout değeri geçersizse
                - Timeout None değilse ve sayısal değilse
                - Timeout <= 0 veya > 3600 ise
            DatabaseConnectionError: Veritabanı bağlantı hatası varsa
            DatabaseQueryError: Veritabanı sorgu hatası varsa
            DatabaseError: Diğer veritabanı hataları
            
        Examples:
            >>> # Basit kullanım - otomatik commit
            >>> with engine.session_context() as session:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     # Otomatik commit ve session kapatma
            
            >>> # Manuel commit (çoklu işlem)
            >>> with engine.session_context(auto_commit=False) as session:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     profile = profile_repo._create(session, user_id=user.id)
            ...     session.commit()  # Manuel commit
            
            >>> # Yüksek izolasyon seviyesi
            >>> with engine.session_context(isolation_level='SERIALIZABLE') as session:
            ...     # Kritik işlem - yüksek izolasyon
            ...     user = user_repo._get_by_id(session, record_id="user123")
            ...     user.balance += 100
            ...     # Otomatik commit
            
            >>> # Query timeout ile
            >>> with engine.session_context(timeout=30.0) as session:
            ...     # 30 saniyeden uzun sorgular iptal edilir
            ...     results = user_repo._get_all(session, limit=1000000)
            
            >>> # Geçersiz timeout değerleri
            >>> try:
            ...     with engine.session_context(timeout=-1) as session:
            ...         pass
            ... except ValueError as e:
            ...     print(e)  # "Timeout must be between 0 and 3600 seconds..."
            
            >>> try:
            ...     with engine.session_context(timeout=5000) as session:
            ...         pass
            ... except ValueError as e:
            ...     print(e)  # "Timeout must be between 0 and 3600 seconds..."
            
            >>> # Hata durumunda otomatik rollback
            >>> with engine.session_context() as session:
            ...     user = user_repo._create(session, email="test@test.com")
            ...     raise ValueError("Hata!")  # Otomatik rollback
            >>> # Kullanıcı veritabanına kaydedilmedi
        
        Note:
            - Repository metodları flush() kullanır ama commit() kullanmaz
            - Bu context manager ile commit otomatik yapılır
            - Hata durumunda otomatik rollback yapılır (transaction güvenliği)
            - Session otomatik kapatılır, manuel kapatmaya gerek yok
            - auto_commit=False kullanırken dikkatli olun, unutulursa değişiklikler kaybolur
            
        Performance Notes:
            - Her context girişinde yeni session oluşturulur
            - Session tracking overhead'i var (weak reference)
            - Timeout ayarı database'e özel komut gerektirir
            
        Related:
            - :meth:`get_session`: Manuel session oluşturma
            - :meth:`with_session`: Decorator versiyonu
            - :class:`DatabaseManager`: Engine yönetimi
        """
        if not self.is_alive:
            error = DatabaseEngineError()
            self._log_error("session_context", error)
            raise error
        
        # Validate connection string integrity
        if not isinstance(self._connection_string, str):
            # CRITICAL: Connection string has been corrupted!
            # This should NEVER happen after successful __init__
            error_details = {
                "method": "session_context",
                "expected_type": "str",
                "actual_type": type(self._connection_string).__name__,
                "actual_value": repr(self._connection_string),
                "config.db_type": self.config.db_type.value if hasattr(self.config, 'db_type') else "unknown",
                "config.db_name": getattr(self.config, 'db_name', "unknown"),
                "engine_id": id(self),
                "engine_is_alive": self.is_alive,
            }
            error_msg = (
                f"CRITICAL BUG DETECTED: _connection_string corrupted!\n"
                f"Expected: str, Got: {type(self._connection_string).__name__}\n"
                f"Value: {repr(self._connection_string)}\n"
                f"Details: {error_details}\n"
                f"This indicates memory corruption or a thread safety issue!"
            )
            logger.critical(f"DatabaseEngine.session_context: {error_msg}")
            raise DatabaseEngineError()
        
        # Timeout validation
        if timeout is not None:
            if not isinstance(timeout, (int, float)):
                error_msg = (
                    f"[DatabaseEngine.session_context] Timeout validation failed!\n"
                    f"  Location: engine.py, line ~1064\n"
                    f"  Method: session_context()\n"
                    f"  Parameter: timeout\n"
                    f"  Expected type: int or float (seconds)\n"
                    f"  Received type: {type(timeout).__name__}\n"
                    f"  Received value: {repr(timeout)}\n"
                    f"  Reason: Timeout must be a numeric value (seconds)\n"
                    f"  Solution: Provide timeout as a number\n"
                    f"  Examples:\n"
                    f"    - session_context(timeout=30)      # 30 seconds\n"
                    f"    - session_context(timeout=300.5)   # 300.5 seconds\n"
                    f"    - session_context(timeout=60*5)    # 5 minutes"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            if not (0 < timeout <= 3600):
                error_msg = (
                    f"[DatabaseEngine.session_context] Timeout validation failed!\n"
                    f"  Location: engine.py, line ~1066\n"
                    f"  Method: session_context()\n"
                    f"  Parameter: timeout\n"
                    f"  Expected range: 0 < timeout <= 3600 (1 hour max)\n"
                    f"  Received value: {timeout}\n"
                    f"  Reason: Timeout must be positive and not exceed 1 hour\n"
                    f"  Solution: Provide a timeout between 0 and 3600 seconds\n"
                    f"  Examples:\n"
                    f"    - session_context(timeout=30)      # 30 seconds\n"
                    f"    - session_context(timeout=300)     # 5 minutes\n"
                    f"    - session_context(timeout=3600)    # 1 hour (max)"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        session = None
        connection = None  # Connection tracking için (isolation level cleanup)
        
        try:
            # Isolation level varsa engine'den execution options ile connection oluştur
            if isolation_level:
                # Connection-level execution options kullan (bind değiştirmek yerine)
                connection = self._engine.connect().execution_options(
                    isolation_level=isolation_level
                )
                # Session'ı bu connection'a bind et
                session = self._session_factory(bind=connection)
            else:
                # Normal session oluştur
                session = self._session_factory()
            
            # Timeout ayarla (PostgreSQL/MySQL)
            if timeout:
                try:
                    # FIXED: Use config.db_type instead of checking _connection_string
                    # This prevents "argument of type 'int' is not iterable" error
                    # because we don't rely on _connection_string being a string
                    from miniflow.database.config.database_type import DatabaseType
                    
                    if self.config.db_type == DatabaseType.POSTGRESQL:
                        session.execute(text(f"SET statement_timeout = {int(timeout * 1000)}"))
                    elif self.config.db_type == DatabaseType.MYSQL:
                        session.execute(text(f"SET SESSION max_execution_time = {int(timeout * 1000)}"))
                    # SQLite doesn't support query timeout, so we skip it
                    
                except Exception as e:
                    logger.warning(f"Failed to set query timeout: {type(e).__name__}: {e}")
                
            self._track_session(session)
            
            yield session
            
            # Post-yield: Auto-flush ve auto-commit işle
            if session.in_transaction():
                try:
                    if auto_flush and session.dirty:
                        session.flush()
                    
                    if auto_commit:
                        session.commit()
                        
                except Exception:
                    raise
                    
        except Exception as e:
            # Herhangi bir hatada rollback yap
            if session and session.in_transaction():
                try:
                    session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}", exc_info=True)
            
            # Veritabanı hatası ise bağlamla yeniden fırlat
            if isinstance(e, (SQLAlchemyError, OperationalError, DBAPIError)):
                error_message = f"Database query failed: {type(e).__name__}: {str(e)}"
                error = DatabaseQueryError(message=error_message)
                self._log_error("session_context", error)
                raise error
            
            # Veritabanı dışı hataları olduğu gibi yeniden fırlat
            self._log_error("session_context", e)
            raise

        finally:
            # Her zaman oturumu kapat
            if session:
                try:
                    session.close()
                    # Manuel olarak untrack et (GC beklemeden)
                    self._untrack_session(session)
                except Exception as e:
                    logger.error(f"Failed to close session: {e}", exc_info=True)
            
            # Isolation level ile oluşturulan connection'ı kapat (memory leak önleme)
            if connection is not None:
                try:
                    connection.close()
                except Exception as e:
                    logger.error(f"Failed to close isolation level connection: {e}", exc_info=True)

    def health_check(self) -> dict:
        """Veritabanı bağlantısı ve engine durumu için sağlık kontrolü yapar.
        
        Bu metod, engine'in durumunu ve veritabanı bağlantısını kontrol eder.
        Production ortamlarında monitoring ve health check endpoint'leri için
        kullanılır. Detaylı durum bilgisi döndürür.
        
        Kontrol Edilenler:
            1. Engine durumu: Başlatılmış mı? (engine_alive)
            2. Aktif session sayısı: Kaç session açık? (active_sessions)
            3. Connection pool bilgileri: Pool durumu (pool_info)
            4. Veritabanı bağlantı testi: SELECT 1 sorgusu (connection_test)
        
        Returns:
            dict: Sağlık durumu bilgisi
                - status (str): 'healthy', 'unhealthy', 'stopped', 'error', 'unknown'
                - engine_alive (bool): Engine başlatılmış mı?
                - active_sessions (int): Aktif session sayısı
                - connection_test (bool): Bağlantı testi başarılı mı?
                - pool_info (dict): Connection pool bilgileri
                    - type (str): Pool tipi (QueuePool, NullPool vb.)
                    - size (int): Pool boyutu
                    - checked_in (int): Pool'da bekleyen connection'lar
                    - checked_out (int): Kullanımda olan connection'lar
                    - overflow (int): Overflow connection'ları
                - error (Optional[str]): Hata mesajı (varsa)
        
        Examples:
            >>> # Health check yapma
            >>> engine.start()
            >>> health = engine.health_check()
            >>> print(health['status'])  # 'healthy'
            >>> print(health['active_sessions'])  # 2
            >>> print(health['pool_info'])  # {'type': 'QueuePool', 'size': 5, ...}
            
            >>> # Engine başlatılmamışsa
            >>> engine = DatabaseEngine(config)
            >>> health = engine.health_check()
            >>> print(health['status'])  # 'stopped'
            >>> print(health['engine_alive'])  # False
            
            >>> # Bağlantı hatası durumu
            >>> # (Veritabanı çökmüşse)
            >>> health = engine.health_check()
            >>> print(health['status'])  # 'unhealthy'
            >>> print(health['connection_test'])  # False
            >>> print(health['error'])  # "connection refused" vb.
            
            >>> # API health check endpoint için
            >>> from fastapi import APIRouter
            >>> router = APIRouter()
            >>> 
            >>> @router.get("/health")
            >>> def health_check_endpoint():
            ...     health = engine.health_check()
            ...     if health['status'] == 'healthy':
            ...         return {"status": "ok", **health}
            ...     else:
            ...         return {"status": "error", **health}, 503
        
        Status Değerleri:
            - 'healthy': Engine başlatılmış ve bağlantı çalışıyor
            - 'unhealthy': Engine başlatılmış ama bağlantı başarısız
            - 'stopped': Engine başlatılmamış
            - 'error': Health check sırasında beklenmeyen hata
            - 'unknown': Başlangıç durumu (normalde görülmez)
        
        Note:
            - Engine başlatılmamışsa status='stopped' döner
            - Bağlantı testi basit bir SELECT 1 sorgusu yapar
            - Pool bilgileri database'e göre değişiklik gösterebilir
            - NullPool kullanılıyorsa pool_info basit bilgi içerir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            
        Use Cases:
            - Kubernetes liveness/readiness probes
            - API health check endpoint'leri
            - Monitoring ve alerting sistemleri
            - Load balancer health checks
            
        Related:
            - :meth:`is_alive`: Basit engine durumu kontrolü
            - :meth:`get_active_session_count`: Session sayısı
            - :meth:`start`: Engine'i başlatır
        """
        result = {
            'status': 'unknown',
            'engine_alive': False,
            'active_sessions': 0,
            'connection_test': False,
            'pool_info': {},
            'error': None
        }
        
        try:
            result['engine_alive'] = self.is_alive
            if not self.is_alive:
                result['status'] = 'stopped'
                return result
            
            result['active_sessions'] = self.get_active_session_count()
            
            # Pool bilgileri ekle
            try:
                pool = self._engine.pool
                from sqlalchemy.pool import NullPool
                
                if isinstance(pool, NullPool):
                    result['pool_info'] = {'type': 'NullPool', 'message': 'No pooling'}
                else:
                    result['pool_info'] = {
                        'type': pool.__class__.__name__,
                        'size': pool.size() if hasattr(pool, 'size') else 'N/A',
                        'checked_in': pool.checkedin() if hasattr(pool, 'checkedin') else 'N/A',
                        'checked_out': pool.checkedout() if hasattr(pool, 'checkedout') else 'N/A',
                        'overflow': getattr(pool, 'overflow', lambda: 'N/A')() if callable(getattr(pool, 'overflow', None)) else getattr(pool, 'overflow', 'N/A'),
                    }
            except Exception as e:
                result['pool_info'] = {'error': str(e)}
            
            # Veritabanı bağlantısını test et (autocommit mode ile, transaction'sız)
            try:
                # Autocommit isolation level kullan (transaction gerektirmez)
                with self._engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as connection:
                    connection.execute(text("SELECT 1"))
                result['connection_test'] = True
                result['status'] = 'healthy'
            except Exception as e:
                result['connection_test'] = False
                result['status'] = 'unhealthy'
                result['error'] = str(e)
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Health check failed: {e}", exc_info=True)
        
        return result
    
    def close_all_sessions(self) -> int:
        """Tüm aktif session'ları kapatır.
        
        Bu metod, weak reference tracking ile takip edilen tüm aktif
        session'ları kapatır. Emergency cleanup veya graceful shutdown
        için kullanılabilir.
        
        Args:
            Yok (parametresiz metod)
            
        Returns:
            int: Kapatılan session sayısı
                - 0: Hiç aktif session yoktu
                - N: N adet session kapatıldı
                
        Raises:
            Exception: Session kapatma hatası (loglanır, fırlatılmaz)
                - Her session için ayrı ayrı denenir
                - Bir session hata verse bile diğerleri kapatılmaya devam eder
                
        Examples:
            >>> # Emergency cleanup
            >>> engine.start()
            >>> session1 = engine.get_session()
            >>> session2 = engine.get_session()
            >>> closed_count = engine.close_all_sessions()
            >>> print(f"{closed_count} session kapatıldı")  # 2
            
            >>> # Graceful shutdown öncesi
            >>> def shutdown():
            ...     active_count = engine.get_active_session_count()
            ...     if active_count > 0:
            ...         closed = engine.close_all_sessions()
            ...         print(f"Shutdown: {closed} session kapatıldı")
            ...     engine.stop()
            
            >>> # Engine başlatılmamışsa
            >>> count = engine.close_all_sessions()
            >>> print(count)  # 0 (uyarı verilir)
        
        Warning:
            ⚠️ Aktif transaction'lar rollback edilmez!
            ⚠️ Pending değişiklikler kaybolur!
            ⚠️ Sadece emergency cleanup için kullanın
            ⚠️ Normal shutdown için stop() kullanın (rollback yapar)
        
        Note:
            - Weak reference tracking kullanır
            - Ölü referanslar otomatik atlanır
            - Her session için ayrı try-except kullanır (hatalı session diğerlerini etkilemez)
            - Thread-safe: RLock kullanır
            - Engine başlatılmamışsa 0 döner ve uyarı verir
            - Tracking listesi temizlenir (_active_sessions.clear())
            
        Comparison with stop():
            - close_all_sessions(): Session'ları kapatır + aktif transaction'ları rollback eder
            - stop(): Session'ları kapatır + rollback + engine dispose + graceful shutdown
            
        When to Use:
            - Emergency cleanup
            - Memory leak cleanup
            - Test ortamında cleanup
            
        When NOT to Use:
            - Normal application shutdown (stop() kullanın)
            - Production cleanup (stop() kullanın)
            
        Related:
            - :meth:`stop`: Graceful shutdown (önerilen)
            - :meth:`get_active_session_count`: Aktif session sayısı
            - :meth:`_track_session`: Session tracking
        """
        if not self.is_alive:
            logger.warning("Cannot close sessions: Engine not started")
            return 0
        
        count = 0
        with self._session_lock:
            for session_ref in list(self._active_sessions):
                session = session_ref()
                if session is not None:
                    try:
                        # Aktif transaction varsa rollback yap (data loss önleme)
                        if session.is_active:
                            session.rollback()
                        session.close()
                        count += 1
                    except Exception as e:
                        logger.warning(f"Error closing session: {e}")
            self._active_sessions.clear()
        
        logger.info(f"Closed {count} active sessions")
        return count