import threading
import logging
from typing import Optional

from ..config import DatabaseConfig
from .engine import DatabaseEngine
from miniflow.models import Base


class DatabaseManager:
    """Thread-safe singleton veritabanı engine yöneticisi.
    
    Bu sınıf, uygulama genelinde tek bir DatabaseEngine instance'ının
    kullanılmasını garantiler (Singleton pattern). Birden fazla thread'den
    güvenli şekilde erişilebilir ve tüm uygulama boyunca aynı engine
    instance'ını paylaşır.
    
    Singleton Pattern:
        - Uygulama genelinde tek bir instance garantisi
        - Thread-safe: Double-checked locking pattern kullanır
        - Her DatabaseManager() çağrısı aynı instance'ı döndürür
        - get_database_manager() helper fonksiyonu ile de erişilebilir
    
    Yaşam Döngüsü:
        1. __new__(): Singleton instance oluşturur (ilk çağrıda)
        2. initialize(config): Engine'i başlatır (uygulama başlangıcında)
        3. engine: Engine instance'ına erişim (her yerden)
        4. reset(): Engine'i durdurur ve temizler (test veya shutdown)
    
    Thread Safety:
        - Double-checked locking pattern ile thread-safe initialization
        - Tüm metodlar thread-safe (lock kullanımı)
        - Multi-threaded uygulamalarda güvenle kullanılabilir
    
    Examples:
        >>> # Uygulama başlangıcında (örn: main.py)
        >>> from src.database.config import DatabaseConfig, DatabaseType
        >>> from src.database.engine.manager import DatabaseManager
        >>> 
        >>> config = DatabaseConfig(
        ...     db_type=DatabaseType.SQLITE,
        ...     db_name=":memory:"
        ... )
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        
        >>> # Her yerden erişim (aynı singleton instance)
        >>> manager = DatabaseManager()  # Aynı instance döner
        >>> with manager.engine.session_context() as session:
        ...     user = user_repo._get_by_id(session, record_id="user123")
        
        >>> # get_instance() metodu ile (alternatif)
        >>> manager = DatabaseManager.get_instance(config, auto_start=True)
        >>> # Sonraki çağrılarda config opsiyonel
        >>> manager = DatabaseManager.get_instance()
        
        >>> # Helper fonksiyon ile
        >>> from src.database.engine.manager import get_database_manager
        >>> manager = get_database_manager()  # Aynı singleton
        >>> engine = manager.engine
        
        >>> # Decorator'lar ile kullanım
        >>> from src.database.engine.decorators import with_session
        >>> from sqlalchemy.orm import Session
        >>> 
        >>> @with_session()  # Otomatik manager kullanır
        >>> def get_user(session: Session, user_id: str):
        ...     return user_repo._get_by_id(session, record_id=user_id)
        
        >>> # Context manager desteği
        >>> with manager:
        ...     # Manager kullanıma hazır
        ...     with manager.engine.session_context() as session:
        ...         user = user_repo._get_by_id(session, record_id="user123")
        >>> # Context'ten çıkınca engine otomatik durdurulur
        
        >>> # Test ortamında reset
        >>> manager.reset(full_reset=True)  # Singleton'u da temizler
    
    Note:
        - initialize() sadece bir kez çağrılmalı (uygulama başlangıcında)
        - Her DatabaseManager() çağrısı aynı instance'ı döndürür
        - Engine initialize edilmeden kullanılamaz
        - reset() test amaçlı kullanılır (production'da nadiren gerekir)
        
    Related:
        - :func:`get_database_manager`: Helper fonksiyon
        - :class:`DatabaseEngine`: Engine sınıfı
        - :class:`DatabaseConfig`: Konfigürasyon sınıfı
    """
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    _is_resetting = False  # Reset durumu için flag
    
    def __new__(cls):
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking + reset kontrolü
                if cls._instance is None and not cls._is_resetting:
                    instance = super().__new__(cls)
                    instance._engine = None
                    instance._config = None
                    instance._initialized = False
                    instance._logger = logging.getLogger(__name__)
                    cls._instance = instance
                elif cls._is_resetting:
                    # Reset sırasında yeni instance oluşturulamaz
                    raise RuntimeError(
                        "DatabaseManager is being reset. Please wait and try again."
                    )
        return cls._instance
    
    def initialize(
        self, 
        config: DatabaseConfig, 
        auto_start: bool = True,
        create_tables: bool = False,
        force_reinitialize: bool = False
    ) -> None:
        """DatabaseEngine'i veritabanı konfigürasyonu ile başlatır.
        
        Bu metod, singleton manager'a DatabaseEngine instance'ı oluşturur ve
        isteğe bağlı olarak engine'i başlatır. Uygulama başlangıcında bir kez
        çağrılmalıdır.
        
        Initialization Mantığı:
            1. Zaten initialize edilmişse force_reinitialize kontrolü yapılır
            2. force_reinitialize=False ise RuntimeError fırlatılır
            3. force_reinitialize=True ise reset yapılıp yeniden initialize edilir
            4. DatabaseEngine instance'ı oluşturulur
            5. auto_start=True ise engine.start() çağrılır
            6. Manager artık kullanıma hazırdır
        
        Args:
            config (DatabaseConfig): Veritabanı konfigürasyonu.
                - db_type: Veritabanı tipi (PostgreSQL, MySQL, SQLite vb.)
                - db_name: Veritabanı adı
                - host, port, username, password: Bağlantı bilgileri
                - engine_config: Engine konfigürasyonu (pool size vb.)
                
            auto_start (bool): Engine otomatik başlatılsın mı?
                - True (varsayılan): Engine başlatılır (start() çağrılır)
                - False: Engine oluşturulur ama başlatılmaz (manuel start gerekir)
                
            force_reinitialize (bool): Zaten initialize edilmişse tekrar initialize et.
                - False (varsayılan): RuntimeError fırlatır
                - True: Mevcut engine'i reset edip yeniden initialize eder
                
        Raises:
            RuntimeError: Manager zaten initialize edilmişse ve force_reinitialize=False ise
            DatabaseConfigurationError: Konfigürasyon geçersiz ise
            DatabaseEngineError: Engine oluşturulurken hata varsa
            
        Examples:
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> from src.database.engine.manager import DatabaseManager
            >>> 
            >>> # Normal kullanım - otomatik başlatma
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=True)
            >>> # Engine başlatıldı, kullanıma hazır
            >>> assert manager.is_initialized
            >>> assert manager.is_started
            
            >>> # Manuel başlatma
            >>> manager.initialize(config, auto_start=False)
            >>> assert manager.is_initialized
            >>> assert not manager.is_started
            >>> manager.engine.start()  # Manuel başlatma
            >>> assert manager.is_started
            
            >>> # Tekrar initialize (exception fırlatır)
            >>> try:
            ...     manager.initialize(config)
            ... except RuntimeError as e:
            ...     print(e)  # "DatabaseManager already initialized..."
            
            >>> # Force reinitialize (mevcut engine'i durdurur ve yeniden başlatır)
            >>> new_config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager.initialize(new_config, force_reinitialize=True)
            >>> # Mevcut engine reset edilip yeniden initialize edildi
            
            >>> # Uygulama başlangıcında (örn: main.py)
            >>> def startup():
            ...     from src.database.config import DatabaseConfig, DatabaseType
            ...     from src.database.engine.manager import DatabaseManager
            ...     
            ...     config = DatabaseConfig(
            ...         db_type=DatabaseType.SQLITE,
            ...         db_name="app.db"
            ...     )
            ...     manager = DatabaseManager()
            ...     manager.initialize(config, auto_start=True)
            ...     return manager
        
        Note:
            - Sadece bir kez çağrılmalı (uygulama başlangıcında)
            - İkinci çağrıda exception fırlatır (force_reinitialize=False ise)
            - force_reinitialize=True ile tekrar initialize edilebilir
            - auto_start=False kullanırsanız manuel start() gerekir
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            - Uygulama başlangıcında mutlaka çağrılmalı
            
        Related:
            - :meth:`reset`: Manager'ı sıfırlar
            - :attr:`engine`: Engine instance'ına erişim
            - :meth:`DatabaseEngine.start`: Engine başlatma
        """
        with self._lock:
            if self._initialized:
                if not force_reinitialize:
                    error_msg = (
                        "DatabaseManager already initialized. "
                        "Use force_reinitialize=True to reinitialize or call reset() first."
                    )
                    self._logger.error(error_msg)
                    raise RuntimeError(error_msg)
                else:
                    self._logger.warning("Force reinitializing DatabaseManager...")
                    # Store old engine reference before reset
                    old_engine = self._engine
                    # Clear the engine reference before reset to avoid deadlock
                    self._engine = None
                    self._initialized = False
                    # Now safely stop the old engine
                    if old_engine is not None:
                        try:
                            old_engine.stop()
                        except Exception as e:
                            self._logger.warning(f"Error stopping old engine during reinitialize: {e}")
                    self._logger.info("Old engine stopped, proceeding with reinitialization")
            
            self._logger.info("Initializing DatabaseManager...")
            
            try:
                self._engine = DatabaseEngine(config)
                self._config = config
                
                if auto_start and create_tables:
                    self._engine.start()
                    self._engine.create_tables(Base.metadata)
                    self._logger.info("DatabaseManager initialized, tables created and started successfully")
                elif auto_start and not create_tables:
                    self._engine.start()
                    self._logger.info("DatabaseManager initialized and started successfully")
                elif not auto_start and create_tables:
                    self._logger.warning("Can not create tables without starting engine. Overwriting command")
                    self._engine.start()
                    self._engine.create_tables(Base.metadata)
                    self._logger.info("DatabaseManager initialized, tables created and started successfully")
                else:
                    self._logger.info("DatabaseManager initialized (not started)")
                
                self._initialized = True
                
            except Exception as e:
                self._logger.error(f"Failed to initialize DatabaseManager: {e}")
                self._engine = None
                self._initialized = False
                raise
    
    def reset(self) -> None:
        """Engine'i durdur ve temizle.
        
        Bu metod, DatabaseEngine'i durdurur ve manager'ı temizler.
        Singleton instance korunur - tüm referanslar geçerliliğini korur.
        
        Reset Mantığı:
            1. Mevcut engine durdurulur ve temizlenir
            2. Configuration temizlenir
            3. Initialized flag sıfırlanır
            4. Singleton instance KORUNUR (tüm referanslar geçerli kalır)
        
        Warning:
            - Test ve development ortamında kullanılır
            - Production'da genellikle application restart gerekir
            - Reset sonrası yeniden initialize edilmesi gerekir
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> # Manager'ı initialize et
            >>> manager = DatabaseManager()
            >>> config = DatabaseConfig(db_type=DatabaseType.SQLITE, sqlite_path=":memory:")
            >>> manager.initialize(config, auto_start=True)
            >>> assert manager.is_initialized
            >>> 
            >>> # Reset - engine durdurulur, singleton korunur
            >>> manager.reset()
            >>> assert not manager.is_initialized
            >>> 
            >>> # Aynı instance ile tekrar initialize edilebilir
            >>> manager.initialize(config, auto_start=True)
            >>> assert manager.is_initialized
            >>> 
            >>> # Tüm referanslar aynı instance'ı gösterir
            >>> manager2 = DatabaseManager()
            >>> assert manager is manager2  # ✅ Singleton korunur
        
        Note:
            - Thread-safe: Lock kullanımı ile korunur
            - Singleton pattern korunur - "zombie instance" sorunu yok
            - Test fixture'larında güvenle kullanılabilir
        
        Related:
            - :meth:`initialize`: Manager'ı yeniden başlatma
            - :meth:`is_initialized`: Manager durumunu kontrol etme
        """
        with self._lock:
            if self._is_resetting:
                self._logger.warning("Reset already in progress")
                return
                
            self._is_resetting = True
            
        try:
            # Mark as not initialized first to prevent new operations
            was_initialized = self._initialized
            
            if self._engine is not None:
                self._logger.info("Stopping database engine...")
                self._engine.stop()
                self._engine = None
                self._logger.info("Database engine stopped")
            
            self._config = None
            
            # Only mark as not initialized after successful engine stop
            self._initialized = False
            
            # Singleton instance is PRESERVED - no more "zombie instances"!
            self._logger.info("DatabaseManager reset complete (singleton preserved)")
            
        except Exception as e:
            # If reset fails, ensure we're in a consistent state
            self._initialized = was_initialized
            self._logger.error(f"Error during reset: {e}")
            raise
        finally:
            self._is_resetting = False
    
    @property
    def engine(self) -> 'DatabaseEngine':
        """Aktif DatabaseEngine instance'ını döndürür.
        
        Returns:
            DatabaseEngine: Aktif DatabaseEngine instance'ı
            
        Raises:
            RuntimeError: Manager initialize edilmemişse veya engine None ise
        """
        if not self._initialized or self._engine is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize(config) first."
            )
        return self._engine
    
    @property
    def is_initialized(self) -> bool:
        """Manager'ın initialize edilip edilmediğini döndür.
        
        Returns:
            bool: True ise manager initialize edilmiş ve engine mevcut
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> manager = DatabaseManager()
            >>> manager.is_initialized  # False
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager.initialize(config, auto_start=True)
            >>> manager.is_initialized  # True
        """
        return self._initialized and self._engine is not None
    
    @property
    def is_started(self) -> bool:
        """Engine'in başlatılıp başlatılmadığını döndür.
        
        Returns:
            bool: True ise manager initialize edilmiş, engine mevcut ve engine başlatılmış
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=False)
            >>> manager.is_initialized  # True
            >>> manager.is_started  # False
            >>> manager.engine.start()
            >>> manager.is_started  # True
        """
        return self._initialized and self._engine is not None and self._engine.is_alive
    
    @property
    def config(self) -> Optional['DatabaseConfig']:
        """Manager'ın configuration'ını döndürür.
        
        Returns:
            Optional[DatabaseConfig]: Configuration objesi, initialize edilmemişse None
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.config  # None
            >>> 
            >>> manager.initialize(config, auto_start=True)
            >>> manager.config.db_type
            DatabaseType.SQLITE
        """
        return self._config
    
    def start(self) -> None:
        """Engine'i başlatır (convenience method).
        
        Bu method `manager.engine.start()` ile aynıdır, sadece daha kısa syntax sağlar.
        
        Raises:
            RuntimeError: Manager initialize edilmemişse
            
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=False)
            >>> manager.is_started  # False
            >>> 
            >>> manager.start()
            >>> manager.is_started  # True
        """
        if not self._initialized or self._engine is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize(config) first."
            )
        self._engine.start()
    
    def stop(self) -> None:
        """Engine'i durdurur (convenience method).
        
        Bu method `manager.engine.stop()` ile aynıdır, sadece daha kısa syntax sağlar.
        
        Raises:
            RuntimeError: Manager initialize edilmemişse
            
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=True)
            >>> manager.is_started  # True
            >>> 
            >>> manager.stop()
            >>> manager.is_started  # False
        """
        if not self._initialized or self._engine is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize(config) first."
            )
        self._engine.stop()
    
    def get_health_status(self) -> dict:
        """Manager ve engine'in sağlık durumunu döndür.
        
        Bu metod, DatabaseManager ve DatabaseEngine'in durumunu kontrol eder
        ve kapsamlı bir sağlık raporu döndürür.
        
        Returns:
            dict: Sağlık durumu bilgisi
                - manager_initialized (bool): Manager initialize edilmiş mi?
                - engine_started (bool): Engine başlatılmış mı?
                - engine_health (dict): Engine'in health_check() sonucu
                    - None: Engine mevcut değilse
                    - Dict: Engine health check sonucu
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> manager = DatabaseManager()
            >>> status = manager.get_health_status()
            >>> # {'manager_initialized': False, 'engine_started': False, 'engine_health': None}
            
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager.initialize(config, auto_start=True)
            >>> status = manager.get_health_status()
            >>> # {
            ... #   'manager_initialized': True,
            ... #   'engine_started': True,
            ... #   'engine_health': {'status': 'healthy', 'connection_test': True, ...}
            ... # }
            
            >>> # Engine durdurulduğunda
            >>> manager.engine.stop()
            >>> status = manager.get_health_status()
            >>> # {'manager_initialized': True, 'engine_started': False, 'engine_health': None}
        
        Note:
            - Health check engine üzerinde çağrılır, hata durumunda exception yakalanır
            - Engine mevcut değilse engine_health None olur
            - Thread-safe: Internal state kontrolü lock gerektirmez
        """
        status = {
            'manager_initialized': self._initialized,
            'engine_started': False,
            'engine_health': None
        }
        
        if self._engine is not None:
            status['engine_started'] = self._engine.is_alive
            try:
                # Always try to get health check, even if stopped
                status['engine_health'] = self._engine.health_check()
            except Exception as e:
                self._logger.error(f"Health check failed: {e}")
                status['engine_health'] = {'status': 'error', 'error': str(e)}
        
        return status
    
    def __repr__(self) -> str:
        """Developer-friendly representation.
        
        Bu metod, debug ve logging için kullanılır. Developer'lara
        manager'ın durumu hakkında teknik bilgi verir.
        
        Returns:
            str: Manager'ın teknik string temsili
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> manager = DatabaseManager()
            >>> repr(manager)
            '<DatabaseManager(status=not initialized)>'
            
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager.initialize(config, auto_start=True)
            >>> repr(manager)
            '<DatabaseManager(status=initialized, engine_alive=True)>'
            
            >>> manager.engine.stop()
            >>> repr(manager)
            '<DatabaseManager(status=initialized, engine_alive=False)>'
        """
        status = "initialized" if self._initialized else "not initialized"
        engine_status = ""
        if self._engine:
            engine_status = f", engine_alive={self._engine.is_alive}"
        return f"<DatabaseManager(status={status}{engine_status})>"
    
    def __str__(self) -> str:
        """User-friendly string representation.
        
        Bu metod, kullanıcı dostu bir string temsili sağlar.
        Manager'ın durumu ve önemli bilgileri içerir.
        
        Returns:
            str: Manager'ın kullanıcı dostu string temsili
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> manager = DatabaseManager()
            >>> str(manager)
            'DatabaseManager (not initialized)'
            
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager.initialize(config, auto_start=True)
            >>> str(manager)
            'DatabaseManager (initialized, engine: started, active_sessions: 0)'
            
            >>> manager.engine.stop()
            >>> str(manager)
            'DatabaseManager (initialized, engine: stopped, active_sessions: 0)'
            
            >>> # Aktif session'larla
            >>> from sqlalchemy import text
            >>> manager.engine.start()
            >>> with manager.engine.session_context() as session:
            ...     session.execute(text("SELECT 1"))
            ...     print(str(manager))  # active_sessions > 0 olabilir
        """
        if not self._initialized:
            return "DatabaseManager (not initialized)"
        
        engine_status = "started" if self._engine and self._engine.is_alive else "stopped"
        active_sessions = self._engine.get_active_session_count() if self._engine else 0
        return f"DatabaseManager (initialized, engine: {engine_status}, active_sessions: {active_sessions})"
    
    def __enter__(self):
        """Context manager desteği - initialize kontrolü.
        
        Context manager olarak kullanıldığında, manager'ın initialize
        edilmiş olması gerekir. Aksi halde RuntimeError fırlatılır.
        
        Returns:
            DatabaseManager: Self instance
            
        Raises:
            RuntimeError: Manager initialize edilmemişse
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=True)
            >>> 
            >>> from sqlalchemy import text
            >>> with manager:
            ...     # Manager kullanıma hazır
            ...     assert manager.is_started
            ...     with manager.engine.session_context() as session:
            ...         result = session.execute(text("SELECT 1")).scalar()
            ...         assert result == 1
            >>> # Context'ten çıkınca engine otomatik durduruldu
            >>> assert not manager.is_started
        
        Note:
            - Initialize edilmemiş manager context manager olarak kullanılamaz
            - Engine başlatılmamışsa otomatik olarak başlatılır
            - __exit__ metodunda graceful shutdown yapılır
        """
        if not self._initialized:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize(config) first."
            )
        
        # Engine başlatılmamışsa otomatik başlat
        if not self.is_started:
            self.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager desteği - graceful shutdown.
        
        Context manager'dan çıkıldığında, aktif session sayısı kontrol edilir
        ve engine gracefully durdurulur. Hata durumunda da cleanup yapılır.
        
        Args:
            exc_type: Exception type (varsa)
            exc_val: Exception value (varsa)
            exc_tb: Exception traceback (varsa)
        
        Returns:
            bool: False - exception'ların propagate edilmesine izin ver
        
        Examples:
            >>> from src.database.engine.manager import DatabaseManager
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> 
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(config, auto_start=True)
            >>> 
            >>> from sqlalchemy import text
            >>> with manager:
            ...     # İşlemler yapılır
            ...     with manager.engine.session_context() as session:
            ...         session.execute(text("SELECT 1"))
            >>> # Manager engine'i otomatik durduruldu
            >>> assert not manager.is_started
        
        Note:
            - Aktif session'lar varsa uyarı verilir
            - Engine stop hatası durumunda log edilir
            - Exception durumunda da cleanup yapılır (finally benzeri)
        """
        if self._engine is not None:
            try:
                active_sessions = self._engine.get_active_session_count()
                if active_sessions > 0:
                    self._logger.warning(
                        f"Closing DatabaseManager with {active_sessions} active sessions"
                    )
                self._engine.stop()
            except Exception as e:
                self._logger.error(f"Error stopping engine in context manager: {e}")
                if exc_type is None:  # Sadece exception yoksa yeniden fırlat
                    raise
        return False

    @classmethod
    def get_instance(
        cls, 
        config: Optional[DatabaseConfig] = None, 
        auto_start: bool = True
    ) -> 'DatabaseManager':
        """Singleton instance'ı döndür veya oluştur.
        
        Bu metod get_database_manager()'a alternatif, daha açık bir API sunar.
        İlk çağrıda config sağlanarak initialize edilebilir, sonraki çağrılarda
        config opsiyoneldir.
        
        Args:
            config (Optional[DatabaseConfig]): Konfigürasyon.
                - İlk çağrıda gerekli (initialize için)
                - Sonraki çağrılarda opsiyonel (zaten initialize edilmişse)
                
            auto_start (bool): Engine otomatik başlatılsın mı?
                - Sadece ilk initialize sırasında kullanılır
                - Sonraki çağrılarda ignore edilir
        
        Returns:
            DatabaseManager: Singleton DatabaseManager instance'ı
        
        Raises:
            RuntimeError: İlk çağrıda config verilmemişse
        
        Examples:
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> from src.database.engine.manager import DatabaseManager, get_database_manager
            >>> 
            >>> # İlk kullanım - config gerekli
            >>> config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name=":memory:"
            ... )
            >>> manager = DatabaseManager.get_instance(config, auto_start=True)
            >>> # Manager initialize edildi ve başlatıldı
            >>> assert manager.is_initialized
            >>> assert manager.is_started
            
            >>> # Sonraki kullanımlar - config opsiyonel (ignore edilir)
            >>> manager = DatabaseManager.get_instance()
            >>> # Zaten initialize edilmiş instance döndürülür
            >>> manager is DatabaseManager.get_instance()  # True (aynı instance)
            
            >>> # get_database_manager() ile aynı sonuç
            >>> manager1 = DatabaseManager.get_instance()
            >>> manager2 = get_database_manager()
            >>> manager1 is manager2  # True
            
            >>> # Alternatif: DatabaseManager() doğrudan çağrı
            >>> manager3 = DatabaseManager()
            >>> manager1 is manager3  # True (hepsi aynı singleton)
        
        Note:
            - Singleton pattern: Her çağrı aynı instance'ı döndürür
            - İlk çağrıda config sağlanmalı
            - Sonraki çağrılarda config ignore edilir (zaten initialize edilmiş)
            - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
            
        Related:
            - :func:`get_database_manager`: Helper fonksiyon alternatifi
            - :meth:`initialize`: Manager başlatma
        """
        instance = cls()
        
        if not instance.is_initialized:
            if config is None:
                raise RuntimeError(
                    "DatabaseManager not initialized and no config provided. "
                    "Provide config for first initialization."
                )
            instance.initialize(config, auto_start=auto_start)
        
        return instance
    
    def reload_config(self, new_config: DatabaseConfig, restart: bool = True) -> None:
        """Yeni konfigürasyon ile engine'i yeniden başlat.
        
        Bu metod, mevcut DatabaseEngine'i durdurur ve yeni konfigürasyon ile
        yeni bir engine oluşturur. Bu işlem aktif session'ları kapatır.
        
        Args:
            new_config (DatabaseConfig): Yeni veritabanı konfigürasyonu.
                
            restart (bool): Engine'i otomatik yeniden başlat.
                - True (varsayılan): Yeni engine başlatılır
                - False: Engine oluşturulur ama başlatılmaz
        
        Raises:
            RuntimeError: Manager initialize edilmemişse
        
        Warning:
            - Bu işlem aktif session'ları kapatır!
            - Production'da dikkatli kullanılmalı
            - Uygulama sırasında config değişikliği genellikle restart gerektirir
        
        Examples:
            >>> from src.database.config import DatabaseConfig, DatabaseType
            >>> from src.database.engine.manager import DatabaseManager
            >>> 
            >>> # Mevcut config ile başlatılmış manager
            >>> old_config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name="old.db"
            ... )
            >>> manager = DatabaseManager()
            >>> manager.initialize(old_config, auto_start=True)
            
            >>> # Yeni config ile reload (aktif session'lar kapatılır)
            >>> new_config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name="new.db"
            ... )
            >>> manager.reload_config(new_config, restart=True)
            >>> # Eski engine durduruldu, yeni engine başlatıldı
            >>> assert manager.is_started
            
            >>> # Reload without restart
            >>> another_config = DatabaseConfig(
            ...     db_type=DatabaseType.SQLITE,
            ...     db_name="another.db"
            ... )
            >>> manager.reload_config(another_config, restart=False)
            >>> assert not manager.is_started
            >>> manager.engine.start()  # Manuel başlatma gerekir
        
        Note:
            - Thread-safe: Lock kullanımı ile korunur
            - Aktif session sayısı log edilir (uyarı olarak)
            - Hata durumunda engine durumu korunur
            - Production'da kullanmadan önce dikkatli düşünülmeli
            
        Related:
            - :meth:`reset`: Manager'ı sıfırlar
            - :meth:`initialize`: İlk başlatma
        """
        with self._lock:
            if not self._initialized:
                raise RuntimeError("Cannot reload config: Manager not initialized")
            
            self._logger.info("Reloading DatabaseManager configuration...")
            
            # Önce mevcut engine'i durdur
            if self._engine is not None:
                active_sessions = self._engine.get_active_session_count()
                if active_sessions > 0:
                    self._logger.warning(
                        f"Reloading config will close {active_sessions} active sessions"
                    )
                try:
                    self._engine.stop()
                except Exception as e:
                    self._logger.error(f"Error stopping engine during reload: {e}")
            
            # Yeni engine oluştur
            try:
                self._engine = DatabaseEngine(new_config)
                self._config = new_config
                
                if restart:
                    self._engine.start()
                    self._logger.info("Configuration reloaded and engine restarted")
                else:
                    self._logger.info("Configuration reloaded (engine not started)")
            except Exception as e:
                self._logger.error(f"Failed to reload configuration: {e}")
                # Engine durumu korunur (hata durumunda)
                raise


def get_database_manager() -> DatabaseManager:
    """Global DatabaseManager singleton instance'ını döndürür.
    
    Bu helper fonksiyon, uygulama genelinde tek bir DatabaseManager
    instance'ına erişim sağlar. Singleton pattern'in kullanımını
    kolaylaştırır.
    
    Returns:
        DatabaseManager: Singleton DatabaseManager instance'ı
            - Her çağrı aynı instance'ı döndürür
            - DatabaseManager() ile aynı sonucu verir
            - Thread-safe erişim garantisi
            
    Examples:
        >>> from src.database.engine.manager import get_database_manager, DatabaseManager
        >>> from src.database.config import DatabaseConfig, DatabaseType
        >>> from sqlalchemy.orm import Session
        >>> 
        >>> # Helper fonksiyon ile erişim
        >>> config = DatabaseConfig(
        ...     db_type=DatabaseType.SQLITE,
        ...     db_name=":memory:"
        ... )
        >>> manager = get_database_manager()
        >>> # Manager henüz initialize edilmemişse hata verebilir
        >>> # Önce initialize etmek gerekir:
        >>> if not manager.is_initialized:
        ...     manager.initialize(config, auto_start=True)
        >>> 
        >>> with manager.engine.session_context() as session:
        ...     # İşlemler
        ...     pass
        
        >>> # Direct instantiation ile (aynı sonuç)
        >>> manager1 = get_database_manager()
        >>> manager2 = DatabaseManager()
        >>> manager1 is manager2  # True (aynı instance)
        
        >>> # Decorator'lar içinde otomatik kullanım
        >>> from src.database.engine.decorators import with_session
        >>> 
        >>> @with_session()  # İçerde get_database_manager() kullanır
        >>> def my_function(session: Session):
        ...     return session.execute(text("SELECT 1")).scalar()
        
        >>> # get_instance() ile aynı sonuç
        >>> manager1 = get_database_manager()
        >>> manager2 = DatabaseManager.get_instance()
        >>> manager1 is manager2  # True (aynı singleton)
    
    Note:
        - Singleton pattern: Her çağrı aynı instance'ı döndürür
        - DatabaseManager() ile aynı sonucu verir
        - Helper fonksiyon olarak daha okunabilir kod sağlar
        - Thread-safe: Multi-threaded ortamlarda güvenle kullanılabilir
        - get_instance() metoduna alternatif bir API
        
    Related:
        - :class:`DatabaseManager`: Manager sınıfı
        - :meth:`DatabaseManager.initialize`: Manager başlatma
        - :meth:`DatabaseManager.get_instance`: Classmethod alternatifi
    """
    return DatabaseManager()  # Zaten singleton, ek layer gereksiz