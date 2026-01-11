from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Type
from sqlalchemy.engine import URL

# -- Imports from local modules -- #
from .database_type import DatabaseType
from .engine_config import EngineConfig
from miniflow.core.exceptions import InvalidInputError, DatabaseConfigurationError
from miniflow.core.logger import get_logger

# Logger instance
logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Veritabanı bağlantı ve engine yapılandırması.

    Birden fazla veritabanı tipini destekler. Bağlantı parametreleri, DB-tipi
    özel `connect_args` birleştirmesi ve genel engine ayarlarını tek bir
    konfigürasyonda toplar.
    """

    # --------------------------------------------------------------
    # CONNECTION PARAMETERS
    # --------------------------------------------------------------
    db_name: str = "miniflow"
    # Veritabanı adı (MySQL/PostgreSQL için). SQLite'ta genelde dosya yolu kullanılır.

    db_type: DatabaseType = DatabaseType.SQLITE
    # Kullanılan veritabanı tipi; URL oluşturma ve varsayılan port seçiminde kullanılır.

    host: str = "localhost"
    # Veritabanı sunucusunun host adı veya IP'si. SQLite için genelde kullanılmaz.

    port: Optional[int] = None
    # Veritabanı portu (ör. PostgreSQL=5432, MySQL=3306). None ise __post_init__ atar.

    username: Optional[str] = None
    # Bağlantı kullanıcı adı. SQLite için genelde None.

    password: Optional[str] = None
    # Bağlantı şifresi. Güvenlik açısından secret manager kullanılması önerilir.


    # --------------------------------------------------------------
    # SQLITE PARAMETERS
    # --------------------------------------------------------------
    sqlite_path: str = "./miniflow.db"
    # SQLite için dosya yolu. ":memory:" kullanılarak bellek içi DB çalıştırılabilir.


    # --------------------------------------------------------------
    # CUSTOM CONNECT ARGS (OVERRIDES)
    # --------------------------------------------------------------
    connect_args: Optional[Dict[str, Any]] = None
    #   Kullanıcının bu DatabaseConfig üzerinde doğrudan belirtebileceği connect_args.
    #   Bu dict, EngineConfig.connect_args + db-type default'ları ile birleştirilir ve en son bu dict
    #   ile override edilir (yani burada verilen anahtarlar önceliklidir).


    # --------------------------------------------------------------
    # ENGINE CONFIGURATION
    # --------------------------------------------------------------
    engine_config: EngineConfig = field(default_factory=EngineConfig)

    
    # --------------------------------------------------------------
    # OPTIONAL DB-SPECIFIC TUNING
    # --------------------------------------------------------------
    application_name: Optional[str] = None
    # PostgreSQL için bağlantı application_name etiketi

    statement_timeout_ms: Optional[int] = None
    # PostgreSQL için statement_timeout değeri (ms cinsinden)

    # EngineConfig: havuz, echo, pre_ping vb. genel engine ayarlarını barındırır.
    # Buradaki connect_args başlangıç olarak get_connect_args() ile birleştirilir.


    # --------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------
    def __post_init__(self):
        """Port ve temel alan doğrulamaları.

        - Port belirtilmemişse `db_type.default_port()` atanır.
        - Port tamsayıya çevrilir; hatalı tipteyse hata verilir.
        - SQLite dışındaki türlerde `host`, `db_name` zorunludur ve `port` > 0 olmalıdır.
        - Kimlik bilgisi gereken türlerde `username` ve `password` zorunludur.
        - PostgreSQL için statement_timeout_ms validation yapılır.
        """
        if self.port is None:
            # DatabaseType.default_port() metodunun int döndüreceği varsayımıyla:
            self.port = self.db_type.default_port()

        # Basit doğrulama: port varsa integer olduğundan emin ol
        if self.port is not None:
            try:
                self.port = int(self.port)
            except (TypeError, ValueError) as e:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Port validation failed!\n"
                    f"  Location: database_config.py, line ~97\n"
                    f"  Field: port\n"
                    f"  Expected type: int\n"
                    f"  Received type: {type(self.port).__name__}\n"
                    f"  Received value: {repr(self.port)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Conversion error: {type(e).__name__}: {e}\n"
                    f"  Solution: Provide a valid integer port number (e.g., 5432 for PostgreSQL, 3306 for MySQL)\n"
                    f"  Example: DatabaseConfig(db_type=DatabaseType.POSTGRESQL, port=5432, ...)"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="port", details=error_msg)
        
        # Credentials validation for DBs that require them (SQLite hariç)
        if self.db_type.requires_credentials():
            if not self.username:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Username validation failed!\n"
                    f"  Location: database_config.py, line ~103\n"
                    f"  Field: username\n"
                    f"  Expected: Non-empty string\n"
                    f"  Received: {repr(self.username)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: {self.db_type.value} requires username for authentication\n"
                    f"  Solution: Provide a valid username\n"
                    f"  Example: DatabaseConfig(db_type=DatabaseType.{self.db_type.name}, username='db_user', ...)"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="username", details=error_msg)
            if self.password is None:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Password validation failed!\n"
                    f"  Location: database_config.py, line ~106\n"
                    f"  Field: password\n"
                    f"  Expected: Non-None value (can be empty string)\n"
                    f"  Received: None\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: {self.db_type.value} requires password for authentication\n"
                    f"  Solution: Provide a password (use empty string '' if no password)\n"
                    f"  Example: DatabaseConfig(db_type=DatabaseType.{self.db_type.name}, password='secret', ...)"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="password", details=error_msg)

        # Non-SQLite validations for host, db_name, port
        if self.db_type != DatabaseType.SQLITE:
            if not self.host:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Host validation failed!\n"
                    f"  Location: database_config.py, line ~110\n"
                    f"  Field: host\n"
                    f"  Expected: Non-empty string (hostname or IP address)\n"
                    f"  Received: {repr(self.host)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: {self.db_type.value} requires a host to connect to\n"
                    f"  Solution: Provide a valid hostname or IP address\n"
                    f"  Example: DatabaseConfig(host='localhost') or DatabaseConfig(host='192.168.1.100')"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="host", details=error_msg)
            if not self.db_name:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Database name validation failed!\n"
                    f"  Location: database_config.py, line ~112\n"
                    f"  Field: db_name\n"
                    f"  Expected: Non-empty string\n"
                    f"  Received: {repr(self.db_name)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: {self.db_type.value} requires a database name to connect to\n"
                    f"  Solution: Provide a valid database name\n"
                    f"  Example: DatabaseConfig(db_name='myapp_db')"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="db_name", details=error_msg)
            if self.port is None or int(self.port) <= 0:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Port validation failed!\n"
                    f"  Location: database_config.py, line ~114\n"
                    f"  Field: port\n"
                    f"  Expected: Positive integer (1-65535)\n"
                    f"  Received: {repr(self.port)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: Port must be a valid port number\n"
                    f"  Solution: Use default port ({self.db_type.default_port()}) or provide a valid port\n"
                    f"  Example: DatabaseConfig(port={self.db_type.default_port()})"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="port", details=error_msg)
        
        # SQLite-specific validations
        if self.db_type == DatabaseType.SQLITE:
            if not self.sqlite_path or not self.sqlite_path.strip():
                error_msg = (
                    f"[DatabaseConfig.__post_init__] SQLite path validation failed!\n"
                    f"  Location: database_config.py, line ~119\n"
                    f"  Field: sqlite_path\n"
                    f"  Expected: Non-empty file path or ':memory:'\n"
                    f"  Received: {repr(self.sqlite_path)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: SQLite requires a file path or ':memory:' for in-memory database\n"
                    f"  Solution: Provide a valid file path\n"
                    f"  Examples:\n"
                    f"    - DatabaseConfig(sqlite_path='./myapp.db')  # File-based\n"
                    f"    - DatabaseConfig(sqlite_path=':memory:')    # In-memory (testing)"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="sqlite_path", details=error_msg)
        
        # PostgreSQL-specific validations
        if self.db_type == DatabaseType.POSTGRESQL and self.statement_timeout_ms is not None:
            try:
                timeout_ms = int(self.statement_timeout_ms)
            except (TypeError, ValueError) as e:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Statement timeout validation failed!\n"
                    f"  Location: database_config.py, line ~125\n"
                    f"  Field: statement_timeout_ms\n"
                    f"  Expected type: int (milliseconds)\n"
                    f"  Received type: {type(self.statement_timeout_ms).__name__}\n"
                    f"  Received value: {repr(self.statement_timeout_ms)}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Conversion error: {type(e).__name__}: {e}\n"
                    f"  Reason: PostgreSQL statement_timeout must be an integer (milliseconds)\n"
                    f"  Solution: Provide timeout in milliseconds\n"
                    f"  Examples:\n"
                    f"    - statement_timeout_ms=30000  # 30 seconds\n"
                    f"    - statement_timeout_ms=60000  # 1 minute"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="statement_timeout_ms", details=error_msg)
            if timeout_ms < 0:
                error_msg = (
                    f"[DatabaseConfig.__post_init__] Statement timeout validation failed!\n"
                    f"  Location: database_config.py, line ~128\n"
                    f"  Field: statement_timeout_ms\n"
                    f"  Expected: Non-negative integer\n"
                    f"  Received: {timeout_ms}\n"
                    f"  Database type: {self.db_type.value}\n"
                    f"  Reason: Timeout cannot be negative\n"
                    f"  Solution: Provide a non-negative timeout value\n"
                    f"  Example: statement_timeout_ms=30000  # 30 seconds"
                )
                logger.error(error_msg)
                raise InvalidInputError(field_name="statement_timeout_ms", details=error_msg)
            self.statement_timeout_ms = timeout_ms
            
    def __repr__(self) -> str:
        """Parolayı saklayan kısa metinsel temsil."""
        if self.db_type == DatabaseType.SQLITE:
            # SQLite için host/port/username bilgileri pek gerekli değil, path öne çıkar.
            return f"DatabaseConfig(type={self.db_type.value}, path={self.sqlite_path})"
        else:
            # Şifreyi yazmıyoruz; yalnızca host/port/db/user gösteriyoruz.
            return f"DatabaseConfig(type={self.db_type.value}, host={self.host}:{self.port}, db={self.db_name}, user={self.username})"

    def get_connection_string(self) -> str:
        """SQLAlchemy uyumlu bağlantı dizesi üretir.

        Kullanıcı adı/şifre kaçışları için `sqlalchemy.engine.URL.create()` kullanılır.
        """
        if self.db_type == DatabaseType.SQLITE:
            # SQLite için üç eğik çizgi: relative path (sqlite:///relative.db)
            # Eğer memory mode isteniyorsa sqlite_path == ":memory:" olarak verilebilir.
            if self.sqlite_path == ":memory:":
                # Multi-threaded testing için shared cache mode kullan
                result = "sqlite:///file::memory:?cache=shared&uri=true"
            else:
                # normalize path — create_engine string olarak kabul edecektir
                result = f"sqlite:///{self.sqlite_path}"
            
            # SQLite için garantili string dönüşümü ve validation
            if not isinstance(result, str):
                result = str(result) if result is not None else ""
            
            if not result:
                raise DatabaseConfigurationError(
                    config_name={
                        "error": "get_connection_string returned empty string for SQLite",
                        "details": {
                            "db_type": self.db_type.value,
                            "sqlite_path": self.sqlite_path,
                        }
                    }
                )
            
            return result
        else:
            # PostgreSQL ve MySQL gibi diğer türler için URL.create kullanımı (güvenli kaçış sağlar)
            drivername = self.db_type.driver_name
            query_params: Dict[str, Any] = {}
            # MySQL için varsayılan charset ekleyelim (gerekirse kullanıcı connect_args ile override edebilir)
            if self.db_type == DatabaseType.MYSQL:
                query_params["charset"] = "utf8mb4"
            # PostgreSQL için application_name ve statement_timeout (options) ekleyelim
            if self.db_type == DatabaseType.POSTGRESQL:
                if self.application_name:
                    query_params["application_name"] = self.application_name
                if self.statement_timeout_ms is not None:
                    # Validation __post_init__'te yapıldı, direkt kullan
                    query_params["options"] = f"-c statement_timeout={self.statement_timeout_ms}ms"

            # FIX: result ataması if bloğunun dışında - hem PostgreSQL hem MySQL için çalışır
            url_result = URL.create(
                drivername=drivername,
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.db_name,
                query=query_params or None
            )
            # GARANTİLİ STRING'E ÇEVİRME
            result = str(url_result) if url_result is not None else ""
            
            # GARANTİLİ STRING'E ÇEVİRME (ekstra güvenlik katmanı)
            # Eğer bir şekilde integer veya başka bir tip gelirse, string'e çevir
            if not isinstance(result, str):
                result = str(result) if result is not None else ""
            
            # CRITICAL VALIDATION: Ensure we're returning a string!
            if not isinstance(result, str):
                error_msg = (
                    f"[DatabaseConfig.get_connection_string] CRITICAL: Non-string connection string!\n"
                    f"  Location: database_config.py, line ~206\n"
                    f"  Method: get_connection_string()\n"
                    f"  Expected type: str\n"
                    f"  Received type: {type(result).__name__}\n"
                    f"  Received value: {repr(result)}\n"
                    f"  Database Configuration:\n"
                    f"    - db_type: {self.db_type.value}\n"
                    f"    - db_name: {self.db_name}\n"
                    f"    - host: {self.host}\n"
                    f"    - port: {self.port}\n"
                    f"    - sqlite_path: {getattr(self, 'sqlite_path', None)}\n"
                    f"  Reason: URL.create() or sqlite path generation returned unexpected type\n"
                    f"  This is a BUG! Connection string must always be a string.\n"
                    f"  Solution: This should never happen. Please report this bug with the above details.\n"
                    f"  Workaround: Check your database configuration parameters."
                )
                logger.critical(error_msg)
                raise DatabaseConfigurationError(
                    config_name={
                        "error": "get_connection_string returned non-string value",
                        "details": error_msg
                    }
                )
            
            # Boş string kontrolü
            if not result:
                error_msg = (
                    f"[DatabaseConfig.get_connection_string] CRITICAL: Empty connection string!\n"
                    f"  Location: database_config.py, line ~224\n"
                    f"  Method: get_connection_string()\n"
                    f"  Expected: Non-empty connection string\n"
                    f"  Received: Empty string ''\n"
                    f"  Database Configuration:\n"
                    f"    - db_type: {self.db_type.value}\n"
                    f"    - db_name: {self.db_name}\n"
                    f"    - host: {self.host}\n"
                    f"    - port: {self.port}\n"
                    f"  Reason: Connection string generation failed\n"
                    f"  Possible causes:\n"
                    f"    1. Invalid database configuration parameters\n"
                    f"    2. URL.create() returned empty string\n"
                    f"    3. SQLite path is invalid\n"
                    f"  Solution: Check your database configuration\n"
                    f"  Examples:\n"
                    f"    - PostgreSQL: DatabaseConfig(db_type=DatabaseType.POSTGRESQL, host='localhost', port=5432, db_name='mydb', username='user', password='pass')\n"
                    f"    - SQLite: DatabaseConfig(db_type=DatabaseType.SQLITE, sqlite_path='./mydb.db')"
                )
                logger.critical(error_msg)
                raise DatabaseConfigurationError(
                    config_name={
                        "error": "get_connection_string returned empty string",
                        "details": error_msg
                    }
                )
            
            return result


    def get_pool_class(self) -> Type:
        """Veritabanı tipine göre uygun pool sınıfını döndürür.
        
        SQLite :memory: için StaticPool kullanılır (tek connection paylaşılır).
        SQLite file-based için NullPool kullanılır (connection pooling yok).
        Diğer veritabanları için QueuePool kullanılır.
        
        Returns:
            Type: SQLAlchemy pool class (QueuePool, NullPool, veya StaticPool)
        """
        if self.db_type == DatabaseType.SQLITE:
            # :memory: database için StaticPool kullan (aynı DB instance paylaşılır)
            if self.sqlite_path == ":memory:":
                return StaticPool
            # File-based SQLite için NullPool
            return NullPool
        return QueuePool


    def get_connect_args(self) -> Dict[str, Any]:
        """DB-tipi özgü `connect_args` birleşimini döndürür.

        Birleşim sırası:
        1) `engine_config.connect_args`
        2) DB-tipi varsayılanları
        3) `DatabaseConfig.connect_args` (override)
        """
        # 1) Base: engine_config.connect_args (kullanıcı engine_config içinde default connect_args belirttiyse al)
        args: Dict[str, Any] = dict(self.engine_config.connect_args or {})

        # 2) DB-specific sensible defaults
        if self.db_type == DatabaseType.SQLITE:
            # SQLite: farklı thread'lerde aynı connection objesinin kullanılmasını engelleyen
            # default davranışı check_same_thread ile kontrol edilir. Multi-threaded uygulamalarda
            # genelde False yapılır (SQLAlchemy pool ile birlikte çalışırken).
            args.setdefault('check_same_thread', False)

        elif self.db_type == DatabaseType.MYSQL:
            # MySQL için kısa bağlantı zaman aşımı değerleri koyuyoruz.
            # Kullanıcı override edebilir.
            args.setdefault('connect_timeout', 10)
            args.setdefault('read_timeout', 30)
            args.setdefault('write_timeout', 30)

        elif self.db_type == DatabaseType.POSTGRESQL:
            # Postgres için connect_timeout gibi ayarları koyabiliriz.
            args.setdefault('connect_timeout', 10)

        # 3) Explicit overrides from DatabaseConfig.connect_args (kullanıcı tarafı)
        if self.connect_args:
            # update() ile gelen anahtarlar önceki değerleri override eder
            args.update(self.connect_args)

        return args

    def to_dict(self) -> Dict[str, Any]:
        """Güvenli ve kapsamlı sözlük temsili.

        Notlar:
        - `password` dahil edilmez.
        - `connect_args` birleşimi uygulanmış değerdir.
        - `engine` kısmı `EngineConfig.to_dict()` çıktısıdır.
        - `connection_string` ve `pool_class` kullanım kolaylığı için eklenir.
        """
        return {
            'db_name': self.db_name,
            'db_type': self.db_type.value,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            # password kasıtlı olarak dahil edilmez
            'sqlite_path': self.sqlite_path,
            'connect_args': self.get_connect_args(),
            'engine': self.engine_config.to_dict(),
            'connection_string': self.get_connection_string(),
            'pool_class': self.get_pool_class().__name__,
            'application_name': self.application_name,
            'statement_timeout_ms': self.statement_timeout_ms,
        }