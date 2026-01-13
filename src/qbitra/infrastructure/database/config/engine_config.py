from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from qbitra.core.exceptions import DatabaseValidationError


@dataclass
class EngineConfig:
    """
    SQLAlchemy engine ve oturum ayarları.

    Bu sınıf, `sqlalchemy.create_engine()` çağrısında kullanılan havuz/bağlantı 
    parametreleri ile ORM oturum (`Session`) davranışlarını tek bir yapı içinde toplar.
    """

    # --------------------------------------------------------------
    # CONNECTION POOL SETTINGS
    # --------------------------------------------------------------
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # --------------------------------------------------------------
    # DEBUG AND LOGGING SETTINGS
    # --------------------------------------------------------------
    echo: bool = False
    echo_pool: bool = False

    # --------------------------------------------------------------
    # SESSION MANAGEMENT SETTINGS
    # --------------------------------------------------------------
    autocommit: bool = False
    autoflush: bool = True
    expire_on_commit: bool = True
    isolation_level: Optional[str] = None
    connect_args: Dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------
    def __post_init__(self):
        """Havuz ve zaman aşımı alanlarını doğrular."""
        for name in ('pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle'):
            value = getattr(self, name)
            try:
                int_value = int(value)
            except (TypeError, ValueError) as e:
                raise DatabaseValidationError(field_name=name, cause=e)
            if int_value < 0:
                raise DatabaseValidationError(field_name=name)
            setattr(self, name, int_value)

    def to_engine_kwargs(self) -> Dict[str, Any]:
        """`sqlalchemy.create_engine` için geçerli anahtarlar."""
        kwargs: Dict[str, Any] = {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'echo': self.echo,
            'echo_pool': self.echo_pool,
        }
        if self.isolation_level is not None:
            kwargs['isolation_level'] = self.isolation_level
        if self.connect_args:
            kwargs['connect_args'] = self.connect_args
        return kwargs

    def to_session_kwargs(self) -> Dict[str, Any]:
        """`sqlalchemy.orm.sessionmaker` / `Session` için anahtarlar."""
        return {
            'autocommit': self.autocommit,
            'autoflush': self.autoflush,
            'expire_on_commit': self.expire_on_commit,
        }