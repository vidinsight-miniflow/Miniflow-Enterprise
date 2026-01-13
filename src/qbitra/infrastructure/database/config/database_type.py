import enum


class DatabaseType(str, enum.Enum):
    """
    Desteklenen veritabanı tipleri.
    
    Bu enum, projede desteklenen veritabanlarını tanımlar ve her tip için 
    varsayılan port, kimlik bilgisi gereksinimi, JSONB/ENUM desteği ile 
    gösterim/driver adları gibi yardımcı bilgileri sağlar.
    """
    
    # --------------------------------------------------------------
    # Enum üyeleri — desteklenen veritabanı tipleri
    # --------------------------------------------------------------
    SQLITE = "sqlite"           # Dosya tabanlı, tek dosyalı küçük veritabanı
    MYSQL = "mysql"             # MySQL (veya MariaDB) sunucu tabanlı veritabanı
    POSTGRESQL = "postgresql"   # PostgreSQL — güçlü JSONB desteğiyle bilinir

    # --------------------------------------------------------------
    # Yardımcı metotlar
    # --------------------------------------------------------------
    def default_port(self) -> int:
        """Varsayılan bağlantı portunu döndürür."""
        ports = {
            DatabaseType.SQLITE: 0,
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
        }
        return ports[self]

    def requires_credentials(self) -> bool:
        """Kullanıcı adı/şifre gerekip gerekmediğini döndürür."""
        return self != DatabaseType.SQLITE

    def supports_jsonb(self) -> bool:
        """JSONB desteği olup olmadığını döndürür (yalnızca PostgreSQL)."""
        return self == DatabaseType.POSTGRESQL

    def supports_native_enum(self) -> bool:
        """Yerel ENUM desteği olup olmadığını döndürür (PostgreSQL, MySQL)."""
        return self in {DatabaseType.POSTGRESQL, DatabaseType.MYSQL}

    # --------------------------------------------------------------
    # Özellikler (properties)
    # --------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Okunabilir gösterim adını döndürür."""
        names = {
            DatabaseType.SQLITE: "SQLite",
            DatabaseType.POSTGRESQL: "PostgreSQL",
            DatabaseType.MYSQL: "MySQL",
        }
        return names[self]

    @property
    def driver_name(self) -> str:
        """SQLAlchemy ile kullanılacak önerilen driver adını döndürür."""
        drivers = {
            DatabaseType.SQLITE: "sqlite",
            DatabaseType.POSTGRESQL: "postgresql",
            DatabaseType.MYSQL: "mysql+pymysql",
        }
        return drivers[self]