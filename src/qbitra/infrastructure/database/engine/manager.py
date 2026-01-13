"""
Veritabanı Yöneticisi Modülü - Singleton Deseni ile Motor Yönetimi

Bu modül, uygulama genelinde veritabanı motoru yönetimi için singleton deseni
uygulaması sağlar. Thread-safe (çoklu iş parçacığı güvenli) ve üretim ortamına 
hazır bir yapı sunar.
"""

import threading
from typing import Optional, Any
from qbitra.infrastructure.database.config import DatabaseConfig
from qbitra.core.exceptions import (
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
)
from qbitra.infrastructure.database.engine.engine import DatabaseEngine
from ..models import metadata




class DatabaseManager:
    """Singleton deseni ile uygulama genelinde tek veritabanı motoru örneği yönetir.
    
    Bu sınıf, thread-safe (çoklu iş parçacığı güvenli) singleton deseni kullanarak 
    uygulama genelinde tek bir DatabaseEngine örneği yönetir. Üretim ortamına hazır 
    bir yapı sunar ve bağlantı havuzu verimliliği sağlar.
    
    Thread Güvenliği:
        - Double-checked locking deseni kullanır (çift kontrol kilitleme)
        - Thread-safe başlatma
        - Thread-safe singleton erişimi
    
    Yaşam Döngüsü:
        1. __new__(): Singleton örneği oluşturur
        2. initialize(): Motoru başlatır
        3. start(): Motoru başlatır (auto_start=False ise)
        4. stop(): Motoru durdurur
        5. reset(): Motoru temizler
    
    Örnekler:
        >>> # Uygulama başlangıcında başlatma
        >>> manager = DatabaseManager()
        >>> manager.initialize(config, auto_start=True)
        >>> 
        >>> # Uygulamanın her yerinden erişim
        >>> manager = DatabaseManager()  # Aynı örnek
        >>> engine = manager.engine
        >>> 
        >>> # Decorator'larla kullanım
        >>> from qbitra.database.engine import with_session
        >>> @with_session()
        >>> def my_function(session):
        ...     # Otomatik olarak manager.engine kullanır
        ...     pass
    """
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    _is_resetting = False
    _engine: Optional[DatabaseEngine] = None
    _config: Optional[DatabaseConfig] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton deseni - her zaman aynı örneği döndürür."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._engine = None
                    cls._instance._config = None
        return cls._instance
    
    def __init__(self):
        """DatabaseManager'ı başlatır (singleton deseni - örnek zaten oluşturulmuş)."""
        # Singleton deseni - __new__ zaten örneği oluşturdu
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Yöneticinin başlatılıp başlatılmadığını kontrol eder."""
        return self._initialized
    
    @property
    def engine(self) -> DatabaseEngine:
        """DatabaseEngine örneğini döndürür.
        
        Raises:
            DatabaseManagerNotInitializedError: Başlatılmamışsa
        """
        if not self._initialized or self._engine is None:
            raise DatabaseManagerNotInitializedError(
                message="DatabaseManager not initialized. Call initialize() first."
            )
        return self._engine
    
    def initialize(
        self,
        config: DatabaseConfig,
        auto_start: bool = True,
        auto_create_tables: bool = False,
        force_reinitialize: bool = False,
    ) -> None:
        """Initialize database engine.
        
        Args:
            config: Database configuration
            auto_start: Automatically start engine after initialization
            auto_create_tables: Create tables from internal metadata if True (default: False)
            force_reinitialize: Force reinitialization if already initialized
        
        Raises:
            DatabaseManagerAlreadyInitializedError: If already initialized and force_reinitialize=False
        """
        if self._initialized and not force_reinitialize:
            raise DatabaseManagerAlreadyInitializedError(
                message="DatabaseManager already initialized. Use force_reinitialize=True to reinitialize."
            )
        
        # Reset if already initialized
        if self._initialized:
            self._reset_internal()
        
        # Store config
        self._config = config
        
        # Create engine
        self._engine = DatabaseEngine(config)
        
        # Mark as initialized
        self._initialized = True
        
        # Auto start if requested
        if auto_start:
            self.start()
        
        # Create tables from internal metadata if requested
        if auto_create_tables:
            # Modelleri import et ki metadata'ya kaydedilsinler
            # qbitra.domain.models import edildiğinde tüm modeller yüklenir ve metadata doldurulur
            import qbitra.domain.models
            
            if self._engine._engine is None:
                self.start()
            # Metadata'yı doğrudan kullan
            metadata.create_all(self._engine._engine)
    
    def start(self) -> None:
        """Veritabanı motorunu başlatır.
        
        Raises:
            DatabaseManagerNotInitializedError: Başlatılmamışsa
        """
        if not self._initialized or self._engine is None:
            raise DatabaseManagerNotInitializedError(
                message="DatabaseManager not initialized. Call initialize() first."
            )
        
        self._engine.start()
    
    def stop(self) -> None:
        """Veritabanı motorunu durdurur (idempotent - birden fazla kez çağrılabilir)."""
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass
    
    def reset(self, full_reset: bool = False) -> None:
        """Veritabanı yöneticisini sıfırlar.
        
        Args:
            full_reset: True ise, singleton örneğini de sıfırla
        """
        self._reset_internal()
        
        if full_reset:
            with self._lock:
                DatabaseManager._instance = None
                DatabaseManager._is_resetting = False
    
    def _reset_internal(self) -> None:
        """Internal reset method."""
        if self._is_resetting:
            return
        
        self._is_resetting = True
        
        try:
            if self._engine is not None:
                self.stop()
                self._engine = None
            
            self._initialized = False
            self._config = None
        finally:
            self._is_resetting = False
    
    def reload_config(
        self,
        config: DatabaseConfig,
        restart: bool = True
    ) -> None:
        """Konfigürasyonu yeniden yükler ve isteğe bağlı olarak motoru yeniden başlatır.
        
        Args:
            config: Yeni veritabanı konfigürasyonu
            restart: Yeniden yükleme sonrası motoru yeniden başlat
        """
        if not self._initialized:
            self.initialize(config, auto_start=restart)
            return
        
        # Stop current engine
        self.stop()
        
        # Update config
        self._config = config
        
        # Create new engine
        self._engine = DatabaseEngine(config)
        
        # Restart if requested
        if restart:
            self.start()
    
    @classmethod
    def get_instance(
        cls,
        config: Optional[DatabaseConfig] = None,
        auto_start: bool = True
    ) -> 'DatabaseManager':
        """Singleton örneğini alır.
        
        Args:
            config: Veritabanı konfigürasyonu (ilk çağrıda gerekli)
            auto_start: Otomatik olarak motoru başlat
        
        Returns:
            DatabaseManager: Singleton örneği
        
        Raises:
            DatabaseManagerNotInitializedError: Başlatılmamışsa ve config verilmemişse
        """
        instance = cls()
        
        if not instance._initialized:
            if config is None:
                raise DatabaseManagerNotInitializedError(
                    message="DatabaseManager not initialized. Provide config on first call."
                )
            instance.initialize(config, auto_start=auto_start)
        
        return instance


def get_database_manager(
    config: Optional[DatabaseConfig] = None,
    auto_start: bool = True
) -> DatabaseManager:
    """DatabaseManager örneğini almak için kolaylık fonksiyonu.
    
    Args:
        config: Veritabanı konfigürasyonu (isteğe bağlı)
        auto_start: Otomatik olarak motoru başlat
    
    Returns:
        DatabaseManager: Singleton örneği
    """
    return DatabaseManager.get_instance(config, auto_start)