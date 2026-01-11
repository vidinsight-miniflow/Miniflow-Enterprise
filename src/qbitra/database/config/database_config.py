from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

from sqlalchemy.engine import URL
from sqlalchemy.pool import QueuePool, NullPool, StaticPool

from qbitra.database.config.database_type import DatabaseType
from qbitra.database.config.engine_config import EngineConfig
from qbitra.core.exceptions import DatabaseValidationError, DatabaseConfigurationError


@dataclass
class DatabaseConfig:
    """
    Veritabanı bağlantı ve engine yapılandırması.
    
    Birden fazla veritabanı tipini destekler. Bağlantı parametreleri, DB-tipi özel 
    `connect_args` birleştirmesi ve genel engine ayarlarını tek bir konfigürasyonda toplar.
    """

    # --------------------------------------------------------------
    # CONNECTION PARAMETERS
    # --------------------------------------------------------------
    db_name: str = "miniflow"
    db_type: DatabaseType = DatabaseType.SQLITE
    host: str = "localhost"
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # --------------------------------------------------------------
    # SQLITE PARAMETERS
    # --------------------------------------------------------------
    sqlite_path: str = "./miniflow.db"

    # --------------------------------------------------------------
    # CUSTOM CONNECT ARGS (OVERRIDES)
    # --------------------------------------------------------------
    connect_args: Optional[Dict[str, Any]] = None

    # --------------------------------------------------------------
    # ENGINE CONFIGURATION
    # --------------------------------------------------------------
    engine_config: EngineConfig = field(default_factory=EngineConfig)

    # --------------------------------------------------------------
    # POSTGRESQL-SPECIFIC TUNING
    # --------------------------------------------------------------
    application_name: Optional[str] = None
    statement_timeout_ms: Optional[int] = None

    # --------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------
    def __post_init__(self):
        """Port ve temel alan doğrulamaları."""
        # Port default ataması
        if self.port is None:
            self.port = self.db_type.default_port()

        # Port validation
        if self.port is not None:
            try:
                self.port = int(self.port)
            except (TypeError, ValueError) as e:
                raise DatabaseValidationError(field_name="port", cause=e)

        # Credentials validation (SQLite hariç)
        if self.db_type.requires_credentials():
            if not self.username:
                raise DatabaseValidationError(field_name="username")
            if self.password is None:
                raise DatabaseValidationError(field_name="password")

        # Non-SQLite validations
        if self.db_type != DatabaseType.SQLITE:
            if not self.host:
                raise DatabaseValidationError(field_name="host")
            if not self.db_name:
                raise DatabaseValidationError(field_name="db_name")
            if self.port is None or self.port <= 0:
                raise DatabaseValidationError(field_name="port")

        # SQLite validation
        if self.db_type == DatabaseType.SQLITE:
            if not self.sqlite_path or not self.sqlite_path.strip():
                raise DatabaseValidationError(field_name="sqlite_path")

        # PostgreSQL statement_timeout validation
        if self.db_type == DatabaseType.POSTGRESQL and self.statement_timeout_ms is not None:
            try:
                timeout_ms = int(self.statement_timeout_ms)
            except (TypeError, ValueError) as e:
                raise DatabaseValidationError(field_name="statement_timeout_ms", cause=e)
            if timeout_ms < 0:
                raise DatabaseValidationError(field_name="statement_timeout_ms")
            self.statement_timeout_ms = timeout_ms

    def __repr__(self) -> str:
        """Parolayı gizleyen kısa metinsel temsil."""
        if self.db_type == DatabaseType.SQLITE:
            return f"DatabaseConfig(type={self.db_type.value}, path={self.sqlite_path})"
        return (
            f"DatabaseConfig(type={self.db_type.value}, "
            f"host={self.host}:{self.port}, db={self.db_name}, user={self.username})"
        )

    def get_connection_string(self) -> str:
        """SQLAlchemy uyumlu bağlantı dizesi üretir."""
        if self.db_type == DatabaseType.SQLITE:
            if self.sqlite_path == ":memory:":
                return "sqlite:///file::memory:?cache=shared&uri=true"
            return f"sqlite:///{self.sqlite_path}"

        query_params: Dict[str, Any] = {}

        if self.db_type == DatabaseType.MYSQL:
            query_params["charset"] = "utf8mb4"

        if self.db_type == DatabaseType.POSTGRESQL:
            if self.application_name:
                query_params["application_name"] = self.application_name
            if self.statement_timeout_ms is not None:
                query_params["options"] = f"-c statement_timeout={self.statement_timeout_ms}ms"

        return str(URL.create(
            drivername=self.db_type.driver_name,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db_name,
            query=query_params or None,
        ))

    def get_pool_class(self):
        """Veritabanı tipine göre uygun pool sınıfını döndürür."""
        if self.db_type == DatabaseType.SQLITE:
            if self.sqlite_path == ":memory:":
                return StaticPool
            return NullPool
        return QueuePool

    def get_connect_args(self) -> Dict[str, Any]:
        """DB-tipi özgü connect_args birleşimini döndürür."""
        args: Dict[str, Any] = dict(self.engine_config.connect_args or {})

        if self.db_type == DatabaseType.SQLITE:
            args.setdefault('check_same_thread', False)
        elif self.db_type == DatabaseType.MYSQL:
            args.setdefault('connect_timeout', 10)
            args.setdefault('read_timeout', 30)
            args.setdefault('write_timeout', 30)
        elif self.db_type == DatabaseType.POSTGRESQL:
            args.setdefault('connect_timeout', 10)

        if self.connect_args:
            args.update(self.connect_args)

        return args