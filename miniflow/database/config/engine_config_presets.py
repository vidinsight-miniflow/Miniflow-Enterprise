from ..config import DatabaseType, EngineConfig


# ==============================================================
# DB_ENGINE_CONFIGS
# --------------------------------------------------------------
# Her desteklenen veritabanı tipi için önerilen EngineConfig
# ayarlarını tutar. Amaç:
#   - Farklı veritabanları için uygun havuz ve bağlantı ayarlarını
#     merkezi biçimde yönetmek (pool, timeout, recycle, isolation).
#   - create_engine() çağrılarında doğru ayarları kolayca almak.
#
# Kullanım:
#   config = DB_ENGINE_CONFIGS[DatabaseType.POSTGRESQL]
#   engine = create_engine(db_url, poolclass=db_cfg.get_pool_class(), **config.to_engine_kwargs())
#   SessionLocal = sessionmaker(bind=engine, **config.to_session_kwargs())
# ==============================================================

DB_ENGINE_CONFIGS = {

    # ==========================================================
    # SQLite yapılandırması
    # ----------------------------------------------------------
    # - Dosya tabanlı, gömülü bir veritabanıdır.
    # - Tek bağlantı mantığıyla çalışır.
    # - Production için önerilmez; test ve küçük projeler içindir.
    # ==========================================================
    DatabaseType.SQLITE: EngineConfig(
        pool_size=1,                # Tek bağlantı yeterlidir.
        max_overflow=0,             # Overflow bağlantı oluşturulmaz.
        pool_timeout=20,            # Kilit durumlarında 20 saniye bekle.
        pool_recycle=0,             # Yenileme gereksiz; 0 ile etkisiz bırak.
        pool_pre_ping=False,        # Dosya tabanlı olduğu için pre-ping gerekli değil.
        connect_args={              # SQLite özgü bağlantı parametreleri
            'check_same_thread': False,
            'timeout': 20
        },
        isolation_level=None,       # Varsayılan isolation seviyesi kullanılır.
    ),


    # ==========================================================
    # PostgreSQL yapılandırması
    # ----------------------------------------------------------
    # - Production ortamlarında yaygındır.
    # - Ağ üzerinden bağlantı sağladığı için pool ve timeout kritik önem taşır.
    # ==========================================================
    DatabaseType.POSTGRESQL: EngineConfig(
        pool_size=20,               # Yüksek eşzamanlılık için geniş havuz.
        max_overflow=30,            # Yoğun trafik anlarında ek kapasite.
        pool_timeout=60,            # Ağ gecikmeleri için 60 sn bekleme.
        pool_recycle=3600,          # 1 saatte bir bağlantıyı yenile.
        pool_pre_ping=True,         # Bağlantı öncesi ping kontrolü.
        connect_args={              # PostgreSQL özgü parametreler
            'connect_timeout': 30,
            'sslmode': 'require',
            'application_name': 'miniflow_app'
        },
        isolation_level='READ_COMMITTED',  # Veri bütünlüğü için güvenli seviye.
    ),


    # ==========================================================
    # MySQL yapılandırması
    # ----------------------------------------------------------
    # - Web uygulamaları ve API sistemlerinde yaygındır.
    # - PyMySQL sürücüsü ile kullanılır.
    # - Pool ve timeout ayarları PostgreSQL’e benzer; recycle genelde daha uzundur.
    # ==========================================================
    DatabaseType.MYSQL: EngineConfig(
        pool_size=15,               # Orta ölçekli uygulamalar için makul havuz.
        max_overflow=25,            # Peak load durumlarında ek kapasite.
        pool_timeout=45,            # Bağlantı almak için bekleme süresi.
        pool_recycle=7200,          # 2 saatte bir bağlantı yenile.
        pool_pre_ping=True,         # Bağlantı öncesi ping kontrolü.
        connect_args={              # MySQL özgü parametreler
            'connect_timeout': 30,
        },
        isolation_level='READ_COMMITTED',  # Dengeli izolasyon seviyesi.
    ),
}