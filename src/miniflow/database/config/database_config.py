from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from sqlalchemy.engine import URL

# -- Imports from local modules -- #
from .database_type import DatabaseType
from .engine_config import EngineConfig
from miniflow.core.exceptions import InvalidInputError, DatabaseConfigurationError


@dataclass
class DatabaseConfig:
    """Veritabanı bağlantı ve engine yapılandırması.

    Birden fazla veritabanı tipini destekler. Bağlantı parametreleri, DB-tipi
    özel `connect_args` birleştirmesi ve genel engine ayarlarını tek bir
    konfigürasyonda toplar.
    """

    # --------------------------------------------------------------
    # CONNECTTION PARAMETERS
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
    # CONNECTTION PARAMETERS
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
            except (TypeError, ValueError):
                raise InvalidInputError(field_name="port")
        
        # Credentials validation for DBs that require them (SQLite hariç)
        if self.db_type.requires_credentials():
            if not self.username:
                raise InvalidInputError(field_name="username")
            if self.password is None:
                raise InvalidInputError(field_name="password")

        # Non-SQLite validations for host, db_name, port
        if self.db_type != DatabaseType.SQLITE:
            if not self.host:
                raise InvalidInputError(field_name="host")
            if not self.db_name:
                raise InvalidInputError(field_name="db_name")
            if self.port is None or int(self.port) <= 0:
                raise InvalidInputError(field_name="port")
        
        # SQLite-specific validations
        if self.db_type == DatabaseType.SQLITE:
            if not self.sqlite_path or not self.sqlite_path.strip():
                raise InvalidInputError(field_name="sqlite_path")
        
        # PostgreSQL-specific validations
        if self.db_type == DatabaseType.POSTGRESQL and self.statement_timeout_ms is not None:
            try:
                timeout_ms = int(self.statement_timeout_ms)
            except (TypeError, ValueError):
                raise InvalidInputError(field_name="statement_timeout_ms")
            if timeout_ms < 0:
                raise InvalidInputError(field_name="statement_timeout_ms")
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
                return "sqlite:///file::memory:?cache=shared&uri=true"
            # normalize path — create_engine string olarak kabul edecektir
            return f"sqlite:///{self.sqlite_path}"

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

        return str(URL.create(
            drivername=drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db_name,
            query=query_params or None
        ))


    def get_pool_class(self):
        """Veritabanı tipine göre uygun pool sınıfını döndürür.
        
        SQLite :memory: için StaticPool kullanılır (tek connection paylaşılır).
        SQLite file-based için NullPool kullanılır (connection pooling yok).
        Diğer veritabanları için QueuePool kullanılır.
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