"""
Database Engine Module - Veritabanı Motoru ve Session Yönetimi

Bu modül, production-ready veritabanı engine yönetimi ve session yönetimi
için araçlar sağlar. SQLAlchemy tabanlı, thread-safe ve ölçeklenebilir
bir veritabanı katmanı sunar.

Ana Bileşenler:
    - DatabaseEngine: SQLAlchemy engine yönetimi ve connection pooling
    - DatabaseManager: Singleton pattern ile engine yönetimi
    - Decorators: Session yönetimi için decorator'lar

Özellikler:
    - Connection Pooling: Verimli bağlantı yönetimi
    - Thread-Safe: Multi-threaded ortamlarda güvenli kullanım
    - Session Management: Otomatik session yaşam döngüsü yönetimi
    - Decorator Pattern: Kolay kullanım için decorator'lar
    - Health Check: Veritabanı durumu kontrolü
    - Graceful Shutdown: Güvenli kaynak temizleme

Hızlı Başlangıç:
    >>> from database.engine import DatabaseManager, get_database_manager
    >>> from database.config import DatabaseConfig, DatabaseType
    >>> 
    >>> # Konfigürasyon oluştur
    >>> config = DatabaseConfig(
    ...     db_type=DatabaseType.POSTGRESQL,
    ...     db_name="mydb",
    ...     host="localhost",
    ...     port=5432,
    ...     username="user",
    ...     password="pass"
    ... )
    >>> 
    >>> # Manager başlat (uygulama başlangıcında)
    >>> manager = get_database_manager()
    >>> manager.initialize(config, auto_start=True)
    >>> 
    >>> # Session kullanımı - Decorator ile
    >>> from database.engine import with_session
    >>> 
    >>> @with_session()
    >>> def get_user(session, user_id: str):
    ...     return user_repo._get_by_id(session, record_id=user_id)
    >>> 
    >>> # Session kullanımı - Context manager ile
    >>> with manager.engine.session_context() as session:
    ...     user = user_repo._create(session, email="test@test.com")

Decorator'lar:
    - with_session: Genel session yönetimi (auto_commit, auto_flush)
    - with_transaction: Atomic transaction garantisi
    - with_readonly_session: Sadece okuma için optimize
    - with_retry_session: Deadlock/timeout için retry desteği
    - inject_session: Keyword argument olarak session inject

Örnekler ve Dokümantasyon:
    - Her sınıf ve fonksiyon detaylı docstring içerir
    - examples/ klasöründe kullanım örnekleri
    - Her decorator için ayrıntılı açıklamalar

Thread Safety:
    Tüm bileşenler thread-safe tasarlanmıştır:
    - DatabaseManager: Double-checked locking pattern
    - DatabaseEngine: RLock ile session tracking
    - Connection pool: SQLAlchemy thread-safe garantisi

Production Ready:
    - Connection pooling
    - Resource cleanup
    - Error handling
    - Health monitoring
    - Graceful shutdown

İlgili Modüller:
    - database.config: Konfigürasyon yönetimi
    - database.repositories: Repository pattern implementasyonu
    - database.utils.exceptions: Özel exception'lar
"""

from .engine import DatabaseEngine, with_retry
from .manager import DatabaseManager, get_database_manager
from .decorators import (
    with_session,
    with_transaction,
    with_readonly_session,
    with_retry_session,
    inject_session,
)


__all__ = [
    'DatabaseEngine',
    'DatabaseManager',
    'get_database_manager',
    'with_retry',
    'with_session',
    'with_transaction',
    'with_readonly_session',
    'with_retry_session',
    'inject_session',
]

