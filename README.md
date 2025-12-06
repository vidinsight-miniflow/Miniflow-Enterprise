# MiniFlow Enterprise

MiniFlow Enterprise, workflow otomasyonu ve yönetimi için geliştirilmiş bir Python/FastAPI tabanlı enterprise API uygulamasıdır.

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Gereksinimler](#gereksinimler)
- [Kurulum](#kurulum)
- [Proje Başlatma](#proje-başlatma)
- [Yapılandırma](#yapılandırma)
- [Dokümantasyon](#dokümantasyon)
- [Mimari](#mimari)
- [Geliştirme](#geliştirme)

---

## ✨ Özellikler

- 🔐 **JWT Authentication** - Güvenli kullanıcı kimlik doğrulama
- 🚦 **Rate Limiting** - IP, User ve API Key bazlı rate limiting
- 📝 **Request Tracing** - X-Request-ID ile request takibi
- ⚠️ **Centralized Error Handling** - Merkezi hata yönetimi
- 📊 **Swagger UI** - Otomatik API dokümantasyonu
- 🔄 **Auto-reload** - Development modunda otomatik yeniden yükleme
- 🏗️ **Workflow Management** - Workflow oluşturma, yönetimi ve execution
- 📜 **Script Management** - Global ve Custom script yönetimi
- 🔗 **Resource Management** - Variable, Credential, Database, File yönetimi
- 👥 **Workspace Management** - Çoklu workspace desteği
- 🎯 **Trigger System** - MANUAL, SCHEDULED, WEBHOOK, EVENT trigger'ları

---

## 🔧 Gereksinimler

### Sistem Gereksinimleri

- **Python:** 3.9 veya üzeri
- **Redis:** Rate limiting ve session yönetimi için (opsiyonel, development için)
- **Database:** 
  - SQLite (local development)
  - PostgreSQL (production önerilir)
  - MySQL (alternatif)

### Python Paketleri

Tüm gerekli paketler `requirements.txt` dosyasında tanımlanmıştır:

```bash
pip install -r requirements.txt
```

**Ana Bağımlılıklar:**
- FastAPI 0.121.3
- SQLAlchemy 2.0.44
- Redis 7.1.0
- PyJWT 2.10.1
- Pydantic 2.12.4
- Uvicorn 0.38.0

---

## 🚀 Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone <repository-url>
cd vidinsight-miniflow-enterprise
```

### 2. Virtual Environment Oluşturun (Önerilir)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Environment Variables Ayarlayın

`.env` dosyası oluşturun:

```bash
# Proje root dizininde .env dosyası oluşturun
cd /path/to/vidinsight-miniflow-enterprise
```

**Otomatik .env Oluşturma (Önerilen):**

```bash
# JWT ve Encryption key'lerini otomatik oluştur
JWT_KEY=$(openssl rand -hex 32)
ENC_KEY=$(openssl rand -hex 32)

cat > .env << EOF
# Application Environment
APP_ENV=local

# Database Configuration
DB_TYPE=sqlite

# Test Key (for configuration validation)
TEST_KEY=ThisKeyIsForConfigTest

# JWT Configuration
JWT_SECRET_KEY=$JWT_KEY
JWT_ALGORITHM=HS256

# Encryption Key
ENCRYPTION_KEY=$ENC_KEY

# Redis Configuration (optional for local development)
REDIS_HOST=localhost
REDIS_PORT=6379

# Mailtrap (optional)
# MAILTRAP_API_KEY=your_mailtrap_api_key
EOF
```

**Manuel .env Oluşturma:**

Eğer `.env.example` dosyası varsa:
```bash
cp .env.example .env
```

Sonra `.env` dosyasını düzenleyin ve secret key'leri oluşturun:

```bash
# JWT Secret Key oluşturma
openssl rand -hex 32

# Encryption Key oluşturma
openssl rand -hex 32
```

**Zorunlu Environment Variables:**
- `APP_ENV`: Uygulama ortamı (local, dev, test, prod)
- `DB_TYPE`: Veritabanı tipi (sqlite, postgresql, mysql)
- `TEST_KEY`: Validation key (değer: `ThisKeyIsForConfigTest`)
- `JWT_SECRET_KEY`: JWT token imzalama için (minimum 32 karakter)
- `ENCRYPTION_KEY`: Veri şifreleme için (minimum 32 karakter)

**Opsiyonel Environment Variables:**
- `CONFIG_PATH`: Configuration dosyası yolu (opsiyonel, default: `./configurations/{APP_ENV}.ini`)
- `MAILTRAP_API_KEY`: Email gönderimi için Mailtrap API key
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `JWT_ALGORITHM`: JWT algoritması (default: HS256)

**Detaylı bilgi için:** `.env.example` dosyasına bakın

### 5. İlk Kurulum (Setup)

İlk kez çalıştırıyorsanız, setup komutunu çalıştırın:

```bash
python -m src.miniflow setup
```

**Setup komutu şunları yapar:**
1. ✅ **Veritabanı Oluşturma:** Tüm tabloları oluşturur (migrations)
2. ✅ **Seed Data:** İlk verileri yükler:
   - User Roles (Owner, Admin, Member)
   - Workspace Plans (Freemium, Starter, Pro, Business, Enterprise)
   - Agreements (Terms of Service, Privacy Policy)
   - Global Scripts (varsayılan script'ler)
3. ✅ **Resources Klasörü:** `resources/` klasör yapısını oluşturur
4. ✅ **Handler Testleri:** Redis ve Mail handler'larını test eder

**Setup Çıktısı:**
```
======================================================================
MINIFLOW SETUP MODE
======================================================================

[1/4] Checking file structure... [OK]
[2/4] Setting up database... [OK]
[3/4] Seeding initial data... [OK]
      • Roles: 3 created, 0 skipped
      • Plans: 5 created, 0 skipped
      • Agreements: 2 created, 0 skipped
      • Global Scripts: X created, 0 skipped
[4/4] Testing handlers... [OK] Redis • Mail [OK]

======================================================================
[SUCCESS] SETUP COMPLETED
======================================================================

Uygulamayı başlatmak için: python -m src.miniflow run
```

---

## 🎯 Proje Başlatma

### PYTHONPATH Ayarlama

**Önemli:** Uygulamayı çalıştırmadan önce PYTHONPATH'i ayarlamanız gerekiyor.

**Yöntem 1: Her seferinde ayarlama (Geçici)**

```bash
cd /path/to/vidinsight-miniflow-enterprise
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Yöntem 2: Kalıcı ayarlama (Önerilen)**

Terminal konfigürasyon dosyanıza ekleyin:

**Mac/Linux (.zshrc veya .bashrc):**
```bash
# ~/.zshrc veya ~/.bashrc dosyasına ekleyin
export PYTHONPATH="${PYTHONPATH}:/path/to/vidinsight-miniflow-enterprise/src"
```

Sonra terminal'i yeniden başlatın veya:
```bash
source ~/.zshrc  # veya source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
# PowerShell profil dosyasına ekleyin
$env:PYTHONPATH = "$env:PYTHONPATH;C:\path\to\vidinsight-miniflow-enterprise\src"
```

### İlk Kurulum (Setup)

**İlk kez çalıştırıyorsanız, mutlaka setup komutunu çalıştırın:**

```bash
# PYTHONPATH ayarlandıktan sonra
python -m src.miniflow setup
```

**Setup komutu şunları yapar:**
1. ✅ **Dosya Yapısı Kontrolü:** Gerekli klasörlerin varlığını kontrol eder
2. ✅ **Veritabanı Oluşturma:** Tüm tabloları oluşturur (migrations)
3. ✅ **Seed Data:** İlk verileri yükler:
   - User Roles (Owner, Admin, Member, Guest)
   - Workspace Plans (Freemium, Starter, Pro, Business, Enterprise)
   - Agreements (Terms of Service, Privacy Policy)
   - Global Scripts (varsayılan script'ler)
4. ✅ **Resources Klasörü:** `resources/` klasör yapısını oluşturur
5. ✅ **Handler Testleri:** Redis ve Mail handler'larını test eder

**Setup Başarılı Çıktısı:**
```
======================================================================
                      [SUCCESS] SETUP COMPLETED                       
======================================================================

Uygulamayı başlatmak için: python -m src.miniflow run
```

### Uygulamayı Başlatma (Run)

**Setup tamamlandıktan sonra uygulamayı başlatın:**

```bash
# PYTHONPATH ayarlandıktan sonra

# Yöntem 1: Komut ile (önerilen)
python -m src.miniflow run

# Yöntem 2: Direkt çalıştırma (default: run)
python -m src.miniflow
```

**Run komutu şunları yapar:**
1. ✅ **Veritabanı Kontrolü:** Veritabanının hazır olup olmadığını kontrol eder
2. ✅ **FastAPI App:** FastAPI uygulamasını oluşturur
3. ✅ **Middleware:** Request ID, Rate Limiting, Exception Handling middleware'lerini ekler
4. ✅ **Routes:** Tüm API route'larını yükler
5. ✅ **Servisler:** Database, Engine, Input Handler, Output Handler servislerini başlatır
6. ✅ **Server:** Uvicorn sunucusunu başlatır

**Run Çıktısı:**
```
======================================================================
MINIFLOW RUN MODE
======================================================================

----------------------------------------------------------------------
WEB SERVER STARTING
----------------------------------------------------------------------
Environment       : LOCAL
Database Type     : SQLITE
Address           : http://127.0.0.1:8000
Documentation     : http://127.0.0.1:8000/docs
Reload            : [ACTIVE]
Workers           : 1
----------------------------------------------------------------------

[WORKER-12345] [1/4] Starting Database...
[WORKER-12345] [1/4] [OK] Database started
[WORKER-12345] [2/4] Starting Engine...
[WORKER-12345] [2/4] [OK] Engine started
[WORKER-12345] [3/4] Starting Output Handler...
[WORKER-12345] [3/4] [OK] Output Handler started
[WORKER-12345] [4/4] Starting Input Handler...
[WORKER-12345] [4/4] [OK] Input Handler started
[WORKER-12345] [SUCCESS] All services started

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Yardım Komutu

Tüm komutları görmek için:

```bash
# PYTHONPATH ayarlandıktan sonra
python -m src.miniflow help
# veya
python -m src.miniflow --help
# veya
python -m src.miniflow -h
```

**Çıktı:**
```
======================================================================
MINIFLOW ENTERPRISE - Available Commands
======================================================================

  setup      Initial setup (database, seed data, tests)
  run        Start application (default)
  help       Show this help message

Examples:
  python -m src.miniflow setup
  python -m src.miniflow run
  python -m src.miniflow        # defaults to 'run'
```

### Sorun Giderme

**"ModuleNotFoundError: No module named 'miniflow'" hatası:**

PYTHONPATH ayarlanmamış. Şu komutu çalıştırın:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**"Database not ready" hatası:**

Setup komutunu çalıştırın:
```bash
python -m src.miniflow setup
```

**Redis bağlantı hatası:**

Redis'in çalıştığından emin olun:
```bash
# Redis kontrolü
redis-cli ping

# Redis başlatma (Mac/Linux)
redis-server

# Redis başlatma (Docker)
docker run -d -p 6379:6379 redis:latest
```

**Port zaten kullanılıyor:**

Farklı bir port kullanın veya mevcut process'i durdurun:
```bash
# Port 8000'i kullanan process'i bul
lsof -i :8000

# Process'i durdur
kill -9 <PID>
```

### Hızlı Başlatma Scripti

Proje root dizininde hazır başlatma scriptleri bulunur. Bu scriptler **otomatik olarak setup kontrolü yapar**:

**Mac/Linux (`start.sh`):**
```bash
# Script'i çalıştırılabilir yap (ilk sefer)
chmod +x start.sh

# Kullanım
./start.sh          # Otomatik: Önce setup, sonra run (setup başarılıysa)
./start.sh run      # Otomatik: Önce setup, sonra run (setup başarılıysa)
./start.sh setup    # Sadece setup yap
./start.sh help     # Yardım için
```

**Windows (`start.bat`):**
```batch
# Kullanım
start.bat           # Otomatik: Önce setup, sonra run (setup başarılıysa)
start.bat run       # Otomatik: Önce setup, sonra run (setup başarılıysa)
start.bat setup     # Sadece setup yap
start.bat help      # Yardım için
```

**Önemli Özellikler:**
- ✅ **Otomatik Setup Kontrolü:** `run` komutu verildiğinde önce setup yapılır
- ✅ **Hata Kontrolü:** Setup başarısız olursa run komutu çalıştırılmaz
- ✅ **PYTHONPATH Otomatik:** PYTHONPATH otomatik ayarlanır, manuel ayarlamaya gerek yok
- ✅ **Kolay Kullanım:** Sadece `./start.sh` veya `start.bat` çalıştırın

**Davranış:**
- `./start.sh` veya `./start.sh run` → Önce setup, başarılıysa run
- `./start.sh setup` → Sadece setup
- Setup başarısız olursa → Run yapılmaz, hata mesajı gösterilir

### API Erişimi

Uygulama başladıktan sonra:

- **API Base URL:** `http://localhost:8000` (veya config'de belirtilen host:port)
- **Swagger UI:** `http://localhost:8000/docs` (development modunda)
- **ReDoc:** `http://localhost:8000/redoc` (development modunda)
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`
- **Health Check:** `http://localhost:8000/health`
- **Root Endpoint:** `http://localhost:8000/`

**Not:** Production modunda Swagger UI ve ReDoc devre dışıdır (güvenlik).

---

## ⚙️ Yapılandırma

### Configuration Dosyaları

Uygulama, `configurations/` klasöründeki `.ini` dosyalarını kullanır:

- **`local.ini`** - Local development için (SQLite, port 8000, reload aktif)
- **`dev.ini`** - Development ortamı için
- **`test.ini`** - Test ortamı için
- **`prod.ini`** - Production ortamı için

**Configuration Dosyası Seçimi:**
- `APP_ENV` environment variable'ına göre otomatik seçilir
- Örnek: `APP_ENV=local` → `configurations/local.ini` kullanılır
- Manuel override: `CONFIG_PATH=./configurations/custom.ini`

### Configuration Bölümleri

**Örnek Configuration (local.ini):**
```ini
[Test]
value = ThisKeyIsForConfigTest

[Database]
db_type = sqlite
db_path = ./miniflow_local.db

[Redis]
host = localhost
port = 6379
db = 0

[Rate Limiting]
ip_requests_per_minute = 1000
user_requests_per_minute = 600

[JWT Settings]
jwt_access_token_expire_minutes = 30
jwt_refresh_token_expire_days = 7

[Server]
host = 127.0.0.1
port = 8000
reload = True
workers = 1
```

**Ana Configuration Bölümleri:**
- `[Database]` - Veritabanı ayarları
- `[Redis]` - Redis connection ayarları
- `[Rate Limiting]` - Rate limiting ayarları
- `[JWT Settings]` - Token expiration ayarları
- `[Server]` - Sunucu ayarları (host, port, reload, workers)
- `[FILE OPERATIONS]` - Dosya yükleme ayarları
- `[WORKFLOW]` - Workflow ayarları
- `[INPUT_HANDLER]` - Execution input handler ayarları
- `[OUTPUT_HANDLER]` - Execution output handler ayarları

---

## 📚 Dokümantasyon

### API Dokümantasyonu

- **Swagger UI:** `http://localhost:8000/docs` (interaktif API dokümantasyonu)
- **ReDoc:** `http://localhost:8000/redoc` (alternatif dokümantasyon)
- **OpenAPI Schema:** `http://localhost:8000/openapi.json` (JSON schema)

### Proje Dokümantasyonu

Proje dokümantasyonu `docs/` klasöründe bulunur:

#### 📁 `docs/routes/` - API Endpoint Dokümantasyonu

Her route için detaylı endpoint dokümantasyonu:
- `agreement_routes.md` - Agreement endpoints
- `auth_routes.md` - Authentication endpoints
- `user_management_routes.md` - User management endpoints
- `workspace_management_routes.md` - Workspace management endpoints
- `workflow_management_routes.md` - Workflow management endpoints
- `execution_management_routes.md` - Execution management endpoints
- ... ve diğerleri

**Detaylar için:** `docs/routes/README.md`

#### 📁 `docs/concepts/` - Konsept Dokümantasyonu

Sistem mimarisi ve konseptler:
- `script_creation_guide.md` - Script oluşturma rehberi
- `workflow_structure.md` - Workflow yapısı ve trigger ilişkileri
- `execution_process.md` - Execution süreci
- `script_node_context_execution_relationship.md` - Script → Node → Context → Execution ilişkisi

**Detaylar için:** `docs/README.md`

---

## 🏗️ Mimari

### Proje Yapısı

```
vidinsight-miniflow-enterprise/
├── configurations/          # Configuration dosyaları (.ini)
├── docs/                   # Dokümantasyon
│   ├── routes/            # API endpoint dokümantasyonu
│   └── concepts/          # Konsept dokümantasyonu
├── seeds/                  # Seed data dosyaları
├── src/
│   └── miniflow/
│       ├── __main__.py     # Ana entry point
│       ├── app.py          # FastAPI app factory
│       ├── core/           # Core utilities (exceptions, logger)
│       ├── database/       # Database yönetimi
│       ├── engine/         # Execution engine
│       ├── handlers/       # Execution handlers
│       ├── models/         # SQLAlchemy modelleri
│       ├── repositories/    # Data access layer
│       ├── scheduler/      # Scheduler servisleri
│       ├── server/         # FastAPI server
│       │   ├── dependencies/  # Dependency injection
│       │   ├── middleware/    # Middleware'ler
│       │   ├── routes/        # API routes
│       │   └── schemas/       # Pydantic schemas
│       ├── services/       # Business logic layer
│       └── utils/         # Utility fonksiyonları
└── tests/                  # Test dosyaları
```

### Servisler

Uygulama başlatıldığında şu servisler otomatik olarak başlatılır:

1. **Database Manager** - Veritabanı bağlantı yönetimi
2. **Engine Manager** - Execution engine yönetimi
3. **ExecutionOutputHandler** - Execution sonuçlarını işleme
4. **ExecutionInputHandler** - Execution input'larını işleme

### Middleware

- **RequestContextMiddleware** - Request context yönetimi (X-Request-ID)
- **IPRateLimitMiddleware** - IP bazlı rate limiting
- **CORSMiddleware** - CORS yönetimi

### Dependency Injection

Servisler `src/miniflow/server/dependencies/service_providers.py` üzerinden sağlanır:
- `@lru_cache` ile singleton pattern
- Merkezi servis yönetimi

---

## 🧪 Geliştirme

### Test Çalıştırma

```bash
# Tüm testler
pytest

# Belirli bir test dosyası
pytest tests/integration/api/test_auth_endpoints.py

# Verbose mod
pytest -v

# Coverage ile
pytest --cov=src/miniflow
```

### Development Modu

Local development için:
- `APP_ENV=local` kullanın
- `reload=True` aktif (otomatik yeniden yükleme)
- SQLite database (hızlı setup)
- Swagger UI aktif

### Production Modu

Production için:
- `APP_ENV=prod` kullanın
- `reload=False` (performans için)
- PostgreSQL/MySQL database
- Swagger UI devre dışı (güvenlik)
- Multiple workers

---

## 🔗 İlgili Dokümantasyon

- **API Dokümantasyonu:** `/docs` (Swagger UI)
- **API Schema:** `/openapi.json`
- **Route Dokümantasyonu:** `docs/routes/`
- **Konsept Dokümantasyonu:** `docs/concepts/`
- **Genel Dokümantasyon:** `docs/README.md`

---

## 📞 Destek

Sorularınız veya önerileriniz için:
- GitHub Issues
- Dokümantasyon sayfası
- API dokümantasyonu

---

**Son Güncelleme:** 2024  
**Versiyon:** 1.0.0  
**Lisans:** [Lisans bilgisi]
