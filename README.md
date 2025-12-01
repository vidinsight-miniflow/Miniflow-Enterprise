# Local Test Kılavuzları - Index

Bu klasör, Miniflow Enterprise API'sinin tüm route'ları için local test kılavuzlarını içerir. Her kılavuz, endpoint'leri test etmek için gerekli tüm bilgileri (headers, route, path variables, request body, response örnekleri) içerir.

---

## 📚 Test Kılavuzları Listesi

### 1. Agreement Routes
**Dosya:** `TEST_KILAVUZU_AGREEMENT.md`  
**Prefix:** `/agreements`  
**Açıklama:** Kullanıcı sözleşmeleri (Terms of Service, Privacy Policy) yönetimi

---

### 2. Authentication Routes
**Dosya:** `TEST_KILAVUZU_AUTH.md`  
**Prefix:** `/auth`  
**Açıklama:** Kullanıcı kaydı, giriş, çıkış, email doğrulama, token yenileme

---

### 3. User Routes
**Dosya:** `TEST_KILAVUZU_USER.md`  
**Prefix:** `/users`  
**Açıklama:** Kullanıcı profil yönetimi, şifre değiştirme, kullanıcı bilgileri

---

### 4. Workspace Routes
**Dosya:** `TEST_KILAVUZU_WORKSPACE.md`  
**Prefix:** `/workspaces`  
**Açıklama:** Workspace CRUD işlemleri, workspace limitleri

---

### 5. Workflow Routes
**Dosya:** `TEST_KILAVUZU_WORKFLOW.md`  
**Prefix:** `/workspaces/{workspace_id}/workflows`  
**Açıklama:** Workflow CRUD işlemleri, workflow execution

---

### 6. API Key Routes
**Dosya:** `TEST_KILAVUZU_API_KEY.md`  
**Prefix:** `/workspaces/{workspace_id}/api-keys`  
**Açıklama:** API key oluşturma, yönetimi, rate limit kontrolü

---

### 7. Variable Routes
**Dosya:** `TEST_KILAVUZU_VARIABLE.md`  
**Prefix:** `/workspaces/{workspace_id}/variables`  
**Açıklama:** Workspace variable'ları (secret/non-secret), encryption/decryption

---

### 8. Workspace Member Routes
**Dosya:** `TEST_KILAVUZU_WORKSPACE_MEMBER.md`  
**Prefix:** `/workspaces/{workspace_id}/members`  
**Açıklama:** Workspace üye yönetimi, rol değiştirme, üye çıkarma

---

### 9. Workspace Invitation Routes
**Dosya:** `TEST_KILAVUZU_WORKSPACE_INVITATION.md`  
**Prefix:** `/workspaces/{workspace_id}/invitations` ve `/invitations`  
**Açıklama:** Workspace davet sistemi, davet kabul/red/iptal

---

### 10. Workspace Plans Routes
**Dosya:** `TEST_KILAVUZU_WORKSPACE_PLANS.md`  
**Prefix:** `/workspace-plans`  
**Açıklama:** Workspace plan'larının API rate limit bilgileri (public endpoint)

---

### 11. Trigger Routes
**Dosya:** `TEST_KILAVUZU_TRIGGER.md`  
**Prefix:** `/workspaces/{workspace_id}/triggers` ve `/workspaces/{workspace_id}/workflows/{workflow_id}/triggers`  
**Açıklama:** Workflow trigger'ları (MANUAL, SCHEDULED, WEBHOOK, EVENT)

---

### 12. Node Routes
**Dosya:** `TEST_KILAVUZU_NODE.md`  
**Prefix:** `/workspaces/{workspace_id}/workflows/{workflow_id}/nodes`  
**Açıklama:** Workflow node'ları, script entegrasyonu, input/output parametreleri

---

### 13. Edge Routes
**Dosya:** `TEST_KILAVUZU_EDGE.md`  
**Prefix:** `/workspaces/{workspace_id}/workflows/{workflow_id}/edges`  
**Açıklama:** Workflow node'ları arası bağlantılar (edge'ler)

---

### 14. File Routes
**Dosya:** `TEST_KILAVUZU_FILE.md`  
**Prefix:** `/workspaces/{workspace_id}/files`  
**Açıklama:** Dosya yükleme, indirme, metadata yönetimi (multipart/form-data)

---

### 15. Credential Routes
**Dosya:** `TEST_KILAVUZU_CREDENTIAL.md`  
**Prefix:** `/workspaces/{workspace_id}/credentials`  
**Açıklama:** API key credential'ları, encryption/decryption (GOOGLE, MICROSOFT, GITHUB)

---

### 16. Database Routes
**Dosya:** `TEST_KILAVUZU_DATABASE.md`  
**Prefix:** `/workspaces/{workspace_id}/databases`  
**Açıklama:** Database connection yönetimi (PostgreSQL, MySQL, MongoDB, vb.), password encryption

---

### 17. Global Script Routes
**Dosya:** `TEST_KILAVUZU_GLOBAL_SCRIPT.md`  
**Prefix:** `/scripts`  
**Açıklama:** Global script'ler (tüm workspace'ler tarafından kullanılabilir), public endpoint'ler

---

### 18. Custom Script Routes
**Dosya:** `TEST_KILAVUZU_CUSTOM_SCRIPT.md`  
**Prefix:** `/workspaces/{workspace_id}/custom-scripts`  
**Açıklama:** Workspace-specific custom script'ler, approval status, test status

---

## 🚀 Uygulamayı Başlatma

### Gereksinimler

- **Python:** 3.9 veya üzeri
- **Redis:** Rate limiting ve session yönetimi için (opsiyonel, development için)
- **Database:** SQLite (local), PostgreSQL veya MySQL (production)

### 1. Environment Variables Ayarlama

Uygulamayı başlatmadan önce gerekli environment variables'ı ayarlayın:

```bash
# .env dosyası oluşturun veya environment variables ayarlayın
export APP_ENV=local          # local, dev, test, prod
export DB_TYPE=sqlite         # sqlite, postgresql, mysql
export CONFIG_PATH=./configurations/local.ini
```

**Önemli Environment Variables:**
- `APP_ENV`: Uygulama ortamı (local, dev, test, prod)
- `DB_TYPE`: Veritabanı tipi (sqlite, postgresql, mysql)
- `CONFIG_PATH`: Configuration dosyası yolu (opsiyonel, default: `./configurations/{APP_ENV}.ini`)

### 2. İlk Kurulum (Setup)

İlk kez çalıştırıyorsanız, setup komutunu çalıştırın:

```bash
python -m src.miniflow setup
```

**Setup komutu şunları yapar:**
1. **Veritabanı Oluşturma:** Tüm tabloları oluşturur (migrations)
2. **Seed Data:** İlk verileri yükler:
   - User Roles (Owner, Admin, Member)
   - Workspace Plans (Freemium, Starter, Pro, Business, Enterprise)
   - Agreements (Terms of Service, Privacy Policy)
3. **Resources Klasörü:** `resources/` klasör yapısını oluşturur
4. **Handler Testleri:** Redis ve Mail handler'larını test eder

**Setup Çıktısı:**
```
======================================================================
MINIFLOW SETUP MODE
======================================================================

[1/4] Creating database structure... ✓ Database OK
[2/4] Creating resources folder... ✓ Resources OK
[3/4] Seeding initial data...
   - User Roles: 3 created, 0 updated, 0 skipped
   - Workspace Plans: 5 created, 0 updated, 0 skipped
   - Agreements: 2 created, 0 updated, 0 skipped
[4/4] Testing handlers... ✓ Redis OK ✓ Mail OK

✅ Setup completed successfully!
```

### 3. Uygulamayı Başlatma (Run)

Setup tamamlandıktan sonra uygulamayı başlatın:

```bash
# Komut ile
python -m src.miniflow run

# Veya direkt (default: run)
python -m src.miniflow
```

**Run komutu şunları yapar:**
1. **Veritabanı Kontrolü:** Veritabanının hazır olup olmadığını kontrol eder
2. **FastAPI App:** FastAPI uygulamasını oluşturur
3. **Middleware:** Request ID, Rate Limiting, Exception Handling middleware'lerini ekler
4. **Routes:** Tüm API route'larını yükler
5. **Server:** Uvicorn sunucusunu başlatır

**Run Çıktısı:**
```
======================================================================
MINIFLOW RUN MODE
======================================================================

----------------------------------------------------------------------
WEB SERVER STARTING
----------------------------------------------------------------------
Environment      : LOCAL
Database Type     : SQLITE
Address           : http://127.0.0.1:8000
Documentation     : http://127.0.0.1:8000/docs
Reload            : ✅ Active
Workers           : 1
----------------------------------------------------------------------

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 4. API Erişimi

Uygulama başladıktan sonra:

- **API Base URL:** `http://localhost:8000` (veya config'de belirtilen host:port)
- **Swagger UI:** `http://localhost:8000/docs`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`
- **Health Check:** `http://localhost:8000/health` (varsa)

### 5. Configuration Dosyaları

Uygulama, `configurations/` klasöründeki `.ini` dosyalarını kullanır:

- **`local.ini`** - Local development için (SQLite, port 8000)
- **`dev.ini`** - Development ortamı için
- **`test.ini`** - Test ortamı için
- **`prod.ini`** - Production ortamı için

**Configuration Bölümleri:**
- `[Database]` - Veritabanı ayarları
- `[JWT Settings]` - Token expiration ayarları
- `[Server]` - Sunucu ayarları (host, port, reload)
- `[file_types]` - İzin verilen/engellenen dosya tipleri

**Örnek Configuration (local.ini):**
```ini
[Database]
db_type = sqlite
db_path = ./miniflow_local.db

[Server]
host = 127.0.0.1
port = 8000
reload = True
workers = 1
```

### 6. Yardım Komutu

Tüm komutları görmek için:

```bash
python -m src.miniflow help
# veya
python -m src.miniflow --help
# veya
python -m src.miniflow -h
```

### 7. Ne Yapar?

**Setup Komutu:**
- ✅ Veritabanı tablolarını oluşturur
- ✅ İlk verileri (seed data) yükler
- ✅ Resources klasör yapısını oluşturur
- ✅ Handler'ları test eder (Redis, Mail)

**Run Komutu:**
- ✅ FastAPI uygulamasını başlatır
- ✅ Tüm middleware'leri aktif eder
- ✅ API route'larını yükler
- ✅ Uvicorn sunucusunu başlatır
- ✅ Auto-reload (development modunda)

**Uygulama Özellikleri:**
- 🔐 JWT Authentication
- 🚦 Rate Limiting (IP, User, API Key bazlı)
- 📝 Request Tracing (X-Request-ID)
- ⚠️ Centralized Error Handling
- 📊 Swagger UI Documentation
- 🔄 Auto-reload (development)

---

## 🚀 Hızlı Başlangıç (API Test)

### 1. Environment Variables Ayarlama (Test Tools)

Postman, Bruno veya benzeri bir tool kullanıyorsanız, aşağıdaki environment variables'ı ayarlayın:

```json
{
  "base_url": "http://localhost:8000",
  "access_token": "",
  "workspace_id": "",
  "workflow_id": "",
  "user_id": "",
  "node_id": "",
  "edge_id": "",
  "file_id": "",
  "credential_id": "",
  "database_id": "",
  "script_id": "",
  "custom_script_id": ""
}
```

### 2. Authentication

Çoğu endpoint Bearer token gerektirir. Önce authentication yapın:

```bash
POST {{base_url}}/auth/login
Body: {
  "email": "user@example.com",
  "password": "password"
}
```

Response'dan `access_token` alın ve environment variable olarak ayarlayın.

### 3. Workspace ID Alma

Workspace ID'yi almak için:

```bash
GET {{base_url}}/users/{{user_id}}/workspaces
Headers: Authorization: Bearer {{access_token}}
```

---

## 📋 Test Senaryoları Öncelik Sırası

Test yaparken aşağıdaki sırayı takip etmeniz önerilir:

1. **Authentication** - Kullanıcı kaydı ve giriş
2. **User** - Kullanıcı profil bilgileri
3. **Workspace** - Workspace oluşturma ve yönetimi
4. **Workspace Member** - Üye ekleme/yönetimi
5. **Workspace Invitation** - Davet sistemi
6. **Variable** - Workspace variable'ları
7. **API Key** - API key oluşturma
8. **Credential** - Credential yönetimi
9. **Database** - Database connection'ları
10. **File** - Dosya yükleme
11. **Global Script** - Global script'leri inceleme
12. **Custom Script** - Custom script oluşturma
13. **Workflow** - Workflow oluşturma
14. **Node** - Node oluşturma
15. **Edge** - Node'lar arası bağlantılar
16. **Trigger** - Trigger oluşturma
17. **Workflow Execution** - Workflow çalıştırma

---

## 🔐 Authentication ve Authorization

### Bearer Token
Çoğu endpoint Bearer token gerektirir:
```
Authorization: Bearer {{access_token}}
```

### API Key
Bazı endpoint'ler API key ile de kullanılabilir:
```
X-API-KEY: {{api_key}}
```

### Workspace Membership
Workspace-scoped endpoint'ler için workspace üyeliği gerekir.

---

## 📝 Kılavuz Formatı

Her test kılavuzu aşağıdaki bölümleri içerir:

1. **Genel Bilgiler** - Base URL, prefix, authentication gereksinimleri
2. **Endpoint Detayları** - Her endpoint için:
   - Method ve Route
   - Headers
   - Path Variables
   - Query Parameters
   - Request Body
   - Success Response
   - Error Response
3. **Test Senaryoları** - Pratik kullanım örnekleri
4. **Postman/Bruno Collection Örnekleri** - Collection yapısı
5. **İlgili Endpoint'ler** - İlişkili route'lar
6. **Notlar** - Önemli bilgiler ve best practices

---

## 🛠️ Kullanılan Araçlar

Bu kılavuzlar aşağıdaki araçlarla kullanılabilir:

- **Postman** - REST API test aracı
- **Bruno** - Açık kaynak API client
- **cURL** - Komut satırı HTTP client
- **HTTPie** - Modern komut satırı HTTP client
- **Insomnia** - REST API client

---

## 📌 Önemli Notlar

1. **Base URL:** Tüm route'larda `{{base_url}}` placeholder'ı kullanılır. Local development için genellikle `http://localhost:8000` olur.

2. **Path Variables:** `{{workspace_id}}`, `{{workflow_id}}` gibi placeholder'lar environment variables'dan alınır.

3. **Request Body:** JSON formatında gönderilir (File upload hariç, multipart/form-data kullanılır).

4. **Response Format:** Tüm response'lar standart format kullanır:
   ```json
   {
     "status": "success|error",
     "code": 200,
     "message": "...",
     "traceId": "...",
     "timestamp": "...",
     "data": { ... }
   }
   ```

5. **Error Handling:** Hata durumlarında `error_message` ve `error_code` döner.

6. **Pagination:** List endpoint'leri pagination destekler (page, page_size).

7. **Filtering:** Çoğu list endpoint'i filtreleme destekler (query parameters).

8. **Soft Delete:** Bazı kaynaklar soft delete kullanır (include_deleted parametresi).

---

## 🔗 İlgili Dokümantasyon

- API dokümantasyonu: `/docs` (Swagger UI)
- API schema: `/openapi.json`
- Ana README: `/README.md`

---

## 📞 Destek

Sorularınız veya önerileriniz için:
- GitHub Issues
- Dokümantasyon sayfası
- API dokümantasyonu

---

**Son Güncelleme:** 2024  
**Versiyon:** 1.0  
**Toplam Route Sayısı:** 18


