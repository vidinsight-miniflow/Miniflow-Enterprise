# MiniFlow Enterprise

MiniFlow Enterprise, workflow otomasyonu ve yönetimi için geliştirilmiş bir Python/FastAPI tabanlı enterprise API uygulamasıdır.

## 📋 İçindekiler

- [Başlamadan Önce](#başlamadan-önce)
- [Adım Adım Kurulum](#adım-adım-kurulum)
- [Environment Variables (.env) Açıklaması](#environment-variables-env-açıklaması)
- [Gerekli Servisler](#gerekli-servisler)
- [Program Başlatma](#program-başlatma)
- [Yapılandırma](#yapılandırma)
- [Sorun Giderme](#sorun-giderme)

---

## 🚀 Başlamadan Önce

### Bu Dokümantasyon Ne İçin?

Bu dokümantasyon, MiniFlow Enterprise'ı **sıfırdan başlayarak** kurmak ve çalıştırmak isteyen herkes için hazırlanmıştır. Her adım detaylı açıklanmıştır.

### Ne Öğreneceksiniz?

1. ✅ Projeyi nasıl klonlayıp kuracağınızı
2. ✅ Gerekli servisleri (Redis, Database) nasıl başlatacağınızı
3. ✅ `.env` dosyasını nasıl oluşturacağınızı ve her değişkenin ne işe yaradığını
4. ✅ Programı nasıl başlatacağınızı
5. ✅ Sorun çıktığında nasıl çözeceğinizi

---

## 📦 Adım Adım Kurulum

### Adım 1: Projeyi İndirin

```bash
# Git ile klonlayın
git clone <repository-url>

# Proje klasörüne girin
cd vidinsight-miniflow-enterprise
```

**Ne yaptık?**
- Projeyi bilgisayarınıza indirdik
- Proje klasörüne geçtik

---

### Adım 2: Python Versiyonunu Kontrol Edin

```bash
# Python versiyonunu kontrol edin (3.9 veya üzeri olmalı)
python --version

# veya
python3 --version
```

**Beklenen Çıktı:**
```
Python 3.9.x
# veya
Python 3.10.x
# veya
Python 3.11.x
# veya
Python 3.12.x
```

**Eğer Python yoksa veya versiyon düşükse:**
- [Python.org](https://www.python.org/downloads/) adresinden yükleyin
- Mac kullanıyorsanız: `brew install python3`
- Linux kullanıyorsanız: `sudo apt-get install python3`

---

### Adım 3: Virtual Environment Oluşturun

**Virtual Environment Nedir?**
- Projenin kendi Python paket ortamıdır
- Sistem Python'unuzu kirletmez
- Her proje için ayrı paket versiyonları kullanabilirsiniz

```bash
# Virtual environment oluştur
python -m venv venv

# Windows'ta aktif et
venv\Scripts\activate

# Mac/Linux'ta aktif et
source venv/bin/activate
```

**Başarılı oldu mu?**
Terminal'inizde `(venv)` yazısı görünmelidir:

```bash
(venv) user@computer:~/vidinsight-miniflow-enterprise$
```

**Eğer görünmüyorsa:**
- Windows: `venv\Scripts\activate.bat` deneyin
- Mac/Linux: `source venv/bin/activate` komutunu tekrar çalıştırın

---

### Adım 4: Bağımlılıkları Yükleyin

**Bağımlılık Nedir?**
- Projenin çalışması için gerekli Python paketleridir
- Örnek: FastAPI, SQLAlchemy, Redis vb.

**Modern Yöntem (Önerilen):**

```bash
# Projeyi editable mode'da kur (PYTHONPATH sorunu çözülür)
pip install -e .
```

**Bu komut ne yapar?**
- ✅ Tüm gerekli paketleri yükler
- ✅ PYTHONPATH'i otomatik ayarlar
- ✅ `miniflow` komutunu kullanılabilir yapar
- ✅ IDE'lerde import'ları otomatik tanır

**Klasik Yöntem (Alternatif):**

```bash
# Sadece paketleri yükle
pip install -r requirements.txt

# PYTHONPATH'i manuel ayarla (her terminalde tekrar gerekir)
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Kurulum ne kadar sürer?**
- İlk kurulum: 2-5 dakika (internet hızına bağlı)
- Sonraki kurulumlar: 30 saniye - 1 dakika

**Kurulum tamamlandı mı?**
```bash
# Kontrol et
miniflow help
```

Eğer `miniflow: command not found` hatası alırsanız, modern yöntemi kullanın: `pip install -e .`

---

### Adım 5: Environment Variables (.env) Oluşturun

**Environment Variables Nedir?**
- Uygulamanın çalışması için gerekli ayarlardır
- Secret key'ler, database bilgileri vb. içerir
- `.env` dosyası olarak saklanır

**Yöntem 1: Quickstart Wizard (En Kolay - Önerilen)**

```bash
miniflow quickstart
```

**Bu komut ne yapar?**
1. İnteraktif olarak ortam seçimi yapar (local, dev, test, prod)
2. Secret key'leri otomatik oluşturur
3. `.env` dosyasını hazırlar

**Örnek Çıktı:**
```
======================================================================
                    MINIFLOW QUICKSTART                    
======================================================================

Ortam seçin:
  1) local  - Yerel geliştirme (varsayılan)
  2) dev    - Development sunucusu
  3) test   - Test ortamı
  4) prod   - Production

Seçim [1]: 1

✅ .env dosyası oluşturuldu (APP_ENV=local)

📋 Sonraki adımlar:
   miniflow setup   # Veritabanını başlat
   miniflow run     # Uygulamayı başlat
```

**Yöntem 2: Manuel Oluşturma**

```bash
# .env.example dosyasını kopyala
cp .env.example .env
```

Sonra `.env` dosyasını bir metin editörü ile açın ve secret key'leri oluşturun:

```bash
# Python ile key oluşturma (tüm platformlarda çalışır)
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_hex(32)}'); print(f'ENCRYPTION_KEY={secrets.token_hex(32)}')"
```

Çıktıyı kopyalayıp `.env` dosyasındaki ilgili satırlara yapıştırın.

---

## 🔐 Environment Variables (.env) Açıklaması

`.env` dosyasındaki her değişkenin ne işe yaradığını açıklıyoruz:

### Zorunlu Değişkenler

#### `APP_ENV`
**Ne işe yarar?** Uygulamanın hangi ortamda çalışacağını belirler.

**Olası değerler:**
- `local` - Yerel geliştirme (SQLite, hot reload aktif)
- `dev` - Development sunucusu
- `test` - Test ortamı
- `prod` - Production (canlı sistem)

**Örnek:**
```bash
APP_ENV=local
```

**Not:** Bu değer, `configurations/` klasöründeki hangi `.ini` dosyasının kullanılacağını belirler.

---

#### `DB_TYPE`
**Ne işe yarar?** Hangi veritabanı sisteminin kullanılacağını belirler.

**Olası değerler:**
- `sqlite` - SQLite (local development için, kurulum gerektirmez)
- `postgresql` - PostgreSQL (production için önerilir)
- `mysql` - MySQL (alternatif)

**Örnek:**
```bash
DB_TYPE=sqlite
```

**Hangi durumda hangisini seçmeliyim?**
- **İlk kez kuruyorsanız:** `sqlite` (en kolay, ekstra kurulum yok)
- **Production için:** `postgresql` veya `mysql` (daha güçlü, ölçeklenebilir)

---

#### `TEST_KEY`
**Ne işe yarar?** Konfigürasyon dosyalarının doğru yüklendiğini kontrol eder.

**Değer:** **ASLA DEĞİŞTİRMEYİN!**
```bash
TEST_KEY=ThisKeyIsForConfigTest
```

**Neden var?**
- Sistem başlarken konfigürasyon dosyalarının doğru yüklendiğini kontrol eder
- Yanlış değer verirseniz uygulama başlamaz

---

#### `JWT_SECRET_KEY`
**Ne işe yarar?** JWT (JSON Web Token) token'larını imzalamak için kullanılır.

**Özellikler:**
- Minimum 32 karakter olmalı
- Güvenli, rastgele bir string olmalı
- **ASLA paylaşmayın veya Git'e commit etmeyin!**

**Nasıl oluşturulur?**
```bash
# Python ile
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL ile (Mac/Linux)
openssl rand -hex 32
```

**Örnek:**
```bash
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Ne olur eğer değiştirirsem?**
- Tüm kullanıcıların token'ları geçersiz olur
- Herkes yeniden giriş yapmak zorunda kalır

---

#### `ENCRYPTION_KEY`
**Ne işe yarar?** Hassas verileri (şifreler, API key'ler vb.) şifrelemek için kullanılır.

**Özellikler:**
- Minimum 32 karakter olmalı
- Güvenli, rastgele bir string olmalı
- **ASLA paylaşmayın veya Git'e commit etmeyin!**

**Nasıl oluşturulur?**
```bash
# Python ile
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL ile (Mac/Linux)
openssl rand -hex 32
```

**Örnek:**
```bash
ENCRYPTION_KEY=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4
```

**Ne olur eğer değiştirirsem?**
- Şifrelenmiş veriler okunamaz hale gelir
- Veritabanındaki şifrelenmiş veriler kaybolur

---

#### `JWT_ALGORITHM`
**Ne işe yarar?** JWT token'larını imzalamak için kullanılan algoritmayı belirler.

**Değer:** Genellikle değiştirmenize gerek yok
```bash
JWT_ALGORITHM=HS256
```

**Diğer olası değerler:**
- `HS256` - HMAC SHA-256 (varsayılan, önerilen)
- `HS384` - HMAC SHA-384
- `HS512` - HMAC SHA-512

---

### Opsiyonel Değişkenler

#### `REDIS_HOST`
**Ne işe yarar?** Redis sunucusunun adresini belirler.

**Varsayılan:** `localhost`
```bash
REDIS_HOST=localhost
```

**Ne zaman değiştirmeliyim?**
- Redis'i farklı bir sunucuda çalıştırıyorsanız
- Docker kullanıyorsanız: `REDIS_HOST=redis` (container adı)

---

#### `REDIS_PORT`
**Ne işe yarar?** Redis sunucusunun port numarasını belirler.

**Varsayılan:** `6379`
```bash
REDIS_PORT=6379
```

**Ne zaman değiştirmeliyim?**
- Redis'i farklı bir portta çalıştırıyorsanız

---

#### `MAILTRAP_API_KEY`
**Ne işe yarar?** Email gönderimi için Mailtrap API key'i.

**Ne zaman gerekli?**
- Email gönderme özelliğini kullanacaksanız
- Kullanıcı kayıt, şifre sıfırlama vb. işlemler için

**Nasıl alınır?**
1. [Mailtrap.io](https://mailtrap.io) adresine kaydolun
2. API key'inizi alın
3. `.env` dosyasına ekleyin

**Örnek:**
```bash
MAILTRAP_API_KEY=your_mailtrap_api_key_here
```

**Eğer eklemezseniz ne olur?**
- Email gönderme özellikleri çalışmaz
- Ancak uygulama çalışmaya devam eder

---

### Örnek .env Dosyası

```bash
# =============================================================================
# MiniFlow Enterprise - Environment Configuration
# =============================================================================

# Uygulama Ortamı
APP_ENV=local

# Veritabanı Tipi
DB_TYPE=sqlite

# Validasyon Key (DEĞİŞTİRME!)
TEST_KEY=ThisKeyIsForConfigTest

# JWT Ayarları
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
JWT_ALGORITHM=HS256

# Şifreleme Key
ENCRYPTION_KEY=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4

# Redis (opsiyonel)
# REDIS_HOST=localhost
# REDIS_PORT=6379

# Mailtrap (opsiyonel)
# MAILTRAP_API_KEY=your_api_key
```

---

## 🛠️ Gerekli Servisler

MiniFlow Enterprise'ın çalışması için bazı servislerin çalışıyor olması gerekir. Hangi servislerin zorunlu, hangilerinin opsiyonel olduğunu açıklıyoruz:

### 1. Python (ZORUNLU)

**Ne işe yarar?** Uygulamanın çalıştığı programlama dili ortamı.

**Kontrol:**
```bash
python --version
```

**Kurulum:**
- [Python.org](https://www.python.org/downloads/) adresinden indirin
- Mac: `brew install python3`
- Linux: `sudo apt-get install python3`

---

### 2. Veritabanı (ZORUNLU)

**Ne işe yarar?** Tüm verilerin (kullanıcılar, workflow'lar, execution'lar vb.) saklandığı yer.

#### Seçenek 1: SQLite (En Kolay - Local Development)

**Avantajlar:**
- ✅ Ekstra kurulum gerektirmez (Python ile birlikte gelir)
- ✅ Dosya tabanlıdır (tek bir `.db` dosyası)
- ✅ Hızlı kurulum

**Kurulum:** Gerekmez, Python ile birlikte gelir.

**Kontrol:** Gerekmez, otomatik çalışır.

**Ne zaman kullanmalıyım?**
- İlk kez kuruyorsanız
- Local development yapıyorsanız
- Tek kullanıcılı test için

---

#### Seçenek 2: PostgreSQL (Production Önerilir)

**Avantajlar:**
- ✅ Güçlü ve ölçeklenebilir
- ✅ Çoklu kullanıcı desteği
- ✅ Production için ideal

**Kurulum:**

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
- [PostgreSQL.org](https://www.postgresql.org/download/windows/) adresinden indirin
- Kurulum sihirbazını takip edin

**Kontrol:**
```bash
# PostgreSQL'in çalıştığını kontrol et
psql --version

# PostgreSQL'e bağlan
psql -U postgres
```

**Ne zaman kullanmalıyım?**
- Production ortamında
- Çoklu kullanıcı desteği gerektiğinde
- Büyük veri setleri ile çalışırken

**Not:** PostgreSQL kullanacaksanız, `.env` dosyasında `DB_TYPE=postgresql` yapın ve `configurations/local.ini` dosyasında database bilgilerini güncelleyin.

---

#### Seçenek 3: MySQL (Alternatif)

**Kurulum:**

**Mac:**
```bash
brew install mysql
brew services start mysql
```

**Linux:**
```bash
sudo apt-get install mysql-server
sudo systemctl start mysql
```

**Kontrol:**
```bash
mysql --version
```

---

### 3. Redis (OPSİYONEL - Ama Önerilir)

**Ne işe yarar?**
- Rate limiting (istek sınırlama)
- Session yönetimi
- Cache (geçici veri saklama)

**Ne zaman gerekli?**
- Rate limiting özelliğini kullanacaksanız
- Session yönetimi yapacaksanız
- Production ortamında

**Local development için:**
- Redis olmadan da çalışır (bazı özellikler devre dışı kalır)
- Ancak production için önerilir

**Kurulum:**

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Windows:**
- [Redis.io](https://redis.io/download) adresinden indirin
- Veya Docker kullanın: `docker run -d -p 6379:6379 redis:latest`

**Kontrol:**
```bash
# Redis'in çalıştığını kontrol et
redis-cli ping
```

**Beklenen Çıktı:**
```
PONG
```

**Eğer hata alırsanız:**
```bash
# Redis'i başlat
redis-server

# Veya Mac'te
brew services start redis

# Veya Linux'ta
sudo systemctl start redis-server
```

**Redis olmadan çalışır mı?**
- Evet, ancak rate limiting ve session yönetimi çalışmaz
- Local development için sorun değil
- Production için önerilir

---

### Servis Durumu Özeti

| Servis | Zorunlu mu? | Local Development | Production |
|--------|-------------|-------------------|------------|
| Python | ✅ Evet | ✅ Gerekli | ✅ Gerekli |
| SQLite | ✅ Evet (local için) | ✅ Yeterli | ❌ Yetersiz |
| PostgreSQL/MySQL | ✅ Evet (prod için) | ⚠️ Opsiyonel | ✅ Gerekli |
| Redis | ⚠️ Opsiyonel | ⚠️ Opsiyonel | ✅ Önerilir |

---

## 🚀 Program Başlatma

### Adım 1: İlk Kurulum (Setup)

**Setup Nedir?**
- Veritabanı tablolarını oluşturur
- İlk verileri (seed data) yükler
- Sistem klasörlerini oluşturur
- Handler'ları test eder

**Ne zaman yapılır?**
- İlk kez kuruyorsanız
- Veritabanını sıfırdan oluşturmak istiyorsanız

**Komut:**
```bash
miniflow setup
```

**Bu komut ne yapar?**

1. **Dosya Yapısı Kontrolü**
   - Gerekli klasörlerin (`configurations/`, `seeds/`, `resources/`) varlığını kontrol eder
   - Eksikse oluşturur

2. **Veritabanı Oluşturma**
   - Tüm tabloları oluşturur (migrations)
   - Veritabanı bağlantısını test eder

3. **Seed Data Yükleme**
   - **User Roles:** Owner, Admin, Member, Guest rolleri
   - **Workspace Plans:** Freemium, Starter, Pro, Business, Enterprise planları
   - **Agreements:** Terms of Service, Privacy Policy metinleri
   - **Global Scripts:** Varsayılan script'ler (matematik işlemleri vb.)

4. **Handler Testleri**
   - Redis bağlantısını test eder
   - Mail handler'ını test eder (opsiyonel)

**Örnek Çıktı:**
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
      • Global Scripts: 6 created, 0 skipped
[4/4] Testing handlers... [OK] Redis • Mail [OK]

======================================================================
[SUCCESS] SETUP COMPLETED
======================================================================

Uygulamayı başlatmak için: miniflow run
```

**Hata alırsanız:**
- `.env` dosyasının doğru oluşturulduğundan emin olun
- Gerekli servislerin (Redis, Database) çalıştığından emin olun
- Hata mesajını okuyun ve [Sorun Giderme](#sorun-giderme) bölümüne bakın

---

### Adım 2: Uygulamayı Başlatma (Run)

**Setup tamamlandıktan sonra uygulamayı başlatın:**

```bash
miniflow run
```

**Veya kısaca:**
```bash
miniflow  # default: run
```

**Bu komut ne yapar?**

1. **Veritabanı Kontrolü**
   - Veritabanının hazır olup olmadığını kontrol eder
   - Eğer hazır değilse hata verir (önce `setup` çalıştırın)

2. **FastAPI Uygulaması Oluşturma**
   - FastAPI app instance'ı oluşturur
   - Middleware'leri ekler (CORS, Rate Limiting, Exception Handling)
   - Route'ları yükler

3. **Servisleri Başlatma**
   - **Database Manager:** Veritabanı bağlantısını başlatır
   - **Engine Manager:** Execution engine'i başlatır
   - **ExecutionOutputHandler:** Execution sonuçlarını işlemek için başlatır
   - **ExecutionInputHandler:** Execution input'larını işlemek için başlatır

4. **Web Sunucusunu Başlatma**
   - Uvicorn web sunucusunu başlatır
   - Belirtilen host ve port'ta dinlemeye başlar

**Örnek Çıktı:**
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

**Başarılı oldu mu?**
- Terminal'de `Uvicorn running on http://127.0.0.1:8000` mesajını görüyorsanız ✅
- Tarayıcıda `http://localhost:8000` adresine gidebilirsiniz
- API dokümantasyonu: `http://localhost:8000/docs`

**Uygulamayı durdurmak için:**
- Terminal'de `Ctrl+C` tuşlarına basın

---

### Adım 3: API'ye Erişim

Uygulama başladıktan sonra şu adreslere erişebilirsiniz:

| Adres | Açıklama |
|-------|----------|
| `http://localhost:8000/` | Ana sayfa (health check) |
| `http://localhost:8000/health` | Sistem sağlık kontrolü |
| `http://localhost:8000/docs` | Swagger UI (interaktif API dokümantasyonu) |
| `http://localhost:8000/redoc` | ReDoc (alternatif dokümantasyon) |
| `http://localhost:8000/openapi.json` | OpenAPI Schema (JSON formatında) |

**Not:** Production modunda (`APP_ENV=prod`) Swagger UI ve ReDoc devre dışıdır (güvenlik nedeniyle).

---

## ⚙️ Yapılandırma

### Configuration Dosyaları

Uygulama, `configurations/` klasöründeki `.ini` dosyalarını kullanır:

| Dosya | Ne Zaman Kullanılır? |
|-------|---------------------|
| `local.ini` | `APP_ENV=local` olduğunda |
| `dev.ini` | `APP_ENV=dev` olduğunda |
| `test.ini` | `APP_ENV=test` olduğunda |
| `prod.ini` | `APP_ENV=prod` olduğunda |

**Nasıl Seçilir?**
- `.env` dosyasındaki `APP_ENV` değişkenine göre otomatik seçilir
- Örnek: `APP_ENV=local` → `configurations/local.ini` kullanılır

**Configuration Dosyası Bölümleri:**

| Bölüm | Ne İçin Kullanılır? |
|-------|-------------------|
| `[Database]` | Veritabanı bağlantı ayarları |
| `[Redis]` | Redis bağlantı ayarları |
| `[Rate Limiting]` | İstek sınırlama ayarları |
| `[JWT Settings]` | Token süre ayarları |
| `[Server]` | Web sunucu ayarları (host, port, reload) |
| `[FILE OPERATIONS]` | Dosya yükleme limitleri |
| `[WORKFLOW]` | Workflow ayarları |
| `[INPUT_HANDLER]` | Execution input handler ayarları |
| `[OUTPUT_HANDLER]` | Execution output handler ayarları |

**Örnek Configuration (local.ini):**
```ini
[Server]
host = 127.0.0.1
port = 8000
reload = True
workers = 1
```

---

## 🔧 Sorun Giderme

### "ModuleNotFoundError: No module named 'miniflow'" Hatası

**Sorun:** Python, `miniflow` modülünü bulamıyor.

**Çözüm 1 (Önerilen):**
```bash
pip install -e .
```

**Çözüm 2:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

---

### "Database not ready" Hatası

**Sorun:** Veritabanı henüz kurulmamış.

**Çözüm:**
```bash
miniflow setup
```

---

### "Redis connection failed" Hatası

**Sorun:** Redis çalışmıyor veya erişilemiyor.

**Çözüm:**

1. **Redis'in çalıştığını kontrol edin:**
```bash
redis-cli ping
```

2. **Eğer çalışmıyorsa başlatın:**
```bash
# Mac
brew services start redis

# Linux
sudo systemctl start redis-server

# Docker
docker run -d -p 6379:6379 redis:latest
```

3. **Eğer Redis kullanmak istemiyorsanız:**
- `.env` dosyasında Redis ayarlarını yorum satırı yapın
- Uygulama çalışır, ancak rate limiting çalışmaz

---

### "Port 8000 already in use" Hatası

**Sorun:** Port 8000 zaten kullanılıyor.

**Çözüm 1: Mevcut Process'i Durdurun**

**Mac/Linux:**
```bash
# Port 8000'i kullanan process'i bul
lsof -i :8000

# Process ID'yi alıp durdur
kill -9 <PID>
```

**Windows:**
```powershell
# Port 8000'i kullanan process'i bul
netstat -ano | findstr :8000

# Process ID'yi alıp durdur
taskkill /PID <PID> /F
```

**Çözüm 2: Farklı Port Kullanın**

`configurations/local.ini` dosyasını açın ve port'u değiştirin:
```ini
[Server]
port = 8001  # 8000 yerine 8001
```

---

### ".env file not found" Hatası

**Sorun:** `.env` dosyası bulunamıyor.

**Çözüm:**
```bash
# Quickstart wizard ile oluştur
miniflow quickstart

# Veya manuel oluştur
cp .env.example .env
# Sonra .env dosyasını düzenleyin
```

---

### "JWT_SECRET_KEY is not set" Hatası

**Sorun:** `.env` dosyasında `JWT_SECRET_KEY` eksik veya yanlış.

**Çözüm:**
```bash
# Key oluştur
python -c "import secrets; print(secrets.token_hex(32))"

# Çıktıyı .env dosyasına ekle
JWT_SECRET_KEY=oluşturulan_key_buraya
```

---

### "Configuration validation failed" Hatası

**Sorun:** Konfigürasyon dosyası yanlış veya eksik.

**Çözüm:**
1. `.env` dosyasında `TEST_KEY=ThisKeyIsForConfigTest` olduğundan emin olun
2. `configurations/` klasöründe ilgili `.ini` dosyasının olduğundan emin olun
3. `APP_ENV` değerinin doğru olduğundan emin olun

---

## 📚 Ek Kaynaklar

### API Dokümantasyonu

- **Swagger UI:** `http://localhost:8000/docs` (uygulama çalışırken)
- **ReDoc:** `http://localhost:8000/redoc` (uygulama çalışırken)

### Proje Dokümantasyonu

- **Route Dokümantasyonu:** `docs/routes/` klasörü
- **Konsept Dokümantasyonu:** `docs/concepts/` klasörü

---

## 🎉 Başarılı Kurulum!

Artık MiniFlow Enterprise'ı başarıyla kurduğunuzu ve çalıştırdığınızı umuyoruz!

**Sonraki Adımlar:**
1. API dokümantasyonunu inceleyin: `http://localhost:8000/docs`
2. İlk kullanıcıyı oluşturun (register endpoint'i ile)
3. İlk workflow'unuzu oluşturun
4. Script'lerinizi yükleyin

**Sorularınız için:**
- GitHub Issues
- Proje dokümantasyonu
- API dokümantasyonu

---

**Son Güncelleme:** 2024  
**Versiyon:** 1.0.0  
