# Script Ekleme Rehberi

Bu dokümantasyon, MiniFlow Enterprise sistemine script eklerken dikkat edilmesi gereken tüm önemli noktaları açıklar.

## İçindekiler

1. [Script Türleri](#script-türleri)
2. [Script Oluşturma Süreci](#script-oluşturma-süreci)
3. [Input ve Output Şemaları](#input-ve-output-şemaları)
4. [Onay Workflow'u](#onay-workflowu)
5. [Önemli Kısıtlamalar](#önemli-kısıtlamalar)
6. [Best Practices](#best-practices)

---

## Script Türleri

MiniFlow Enterprise'da iki tür script vardır:

### 1. Global Scripts (Genel Scriptler)
- **Erişim**: Tüm workspace'ler tarafından kullanılabilir
- **Yönetim**: Sadece admin kullanıcılar oluşturabilir/güncelleyebilir
- **Onay**: Onay workflow'u yoktur (admin tarafından oluşturulduğu için)
- **Kullanım**: Her workspace'den erişilebilir
- **Endpoint**: `/frontend/admin/scripts`

### 2. Custom Scripts (Workspace Scriptleri)
- **Erişim**: Sadece oluşturulduğu workspace'de kullanılabilir
- **Yönetim**: Workspace üyeleri oluşturabilir
- **Onay**: PENDING → APPROVED/REJECTED workflow'u vardır
- **Kullanım**: Sadece kendi workspace'inde
- **Endpoint**: `/frontend/workspaces/{workspace_id}/scripts`

---

## Script Oluşturma Süreci

### Custom Script Oluşturma

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/scripts`

**Gerekli Alanlar:**
- `name` (string, required): Script adı (workspace içinde benzersiz olmalı)
- `content` (string, required): Python script içeriği

**Opsiyonel Alanlar:**
- `description` (string): Script açıklaması
- `category` (string): Kategori
- `subcategory` (string): Alt kategori
- `required_packages` (List[string]): Gerekli Python paketleri
- `input_schema` (Dict[str, Any]): Input şeması (JSON)
- `output_schema` (Dict[str, Any]): Output şeması (JSON)
- `tags` (List[string]): Etiketler
- `documentation_url` (string): Dökümantasyon URL'i

**Süreç:**
1. **Validasyon**: Name ve content boş olamaz
2. **Workspace Kontrolü**: Workspace var mı kontrol edilir
3. **Limit Kontrolü**: Workspace'in custom script limiti kontrol edilir
4. **Benzersizlik Kontrolü**: Aynı isimde script var mı kontrol edilir
5. **Dosya Yükleme**: Script içeriği diske `.py` uzantılı dosya olarak yazılır
6. **Veritabanı Kaydı**: Script PENDING approval status ile oluşturulur
7. **Workspace Güncelleme**: Workspace'in `current_custom_script_count` değeri artırılır

**Örnek Request:**
```json
{
  "name": "data_processor",
  "content": "def module():\n    class Processor:\n        def run(self, params):\n            return {'result': params.get('data', '')}\n    return Processor()",
  "description": "Data processing script",
  "category": "data",
  "input_schema": {
    "data": {
      "type": "string",
      "required": true,
      "description": "Input data to process"
    }
  },
  "output_schema": {
    "result": {
      "type": "string",
      "description": "Processed result"
    }
  },
  "required_packages": ["pandas", "numpy"],
  "tags": ["data", "processing"]
}
```

---

## Input ve Output Şemaları

### Input Schema Formatı

Input schema, script'in çalışma zamanında alacağı parametreleri tanımlar. Node oluşturulurken bu şemaya göre `input_params` validate edilir.

**Format:**
```json
{
  "param_name": {
    "type": "string|number|integer|float|boolean|array|object|email|url|password",
    "required": true|false,
    "default": "default_value",
    "description": "Parameter description",
    "placeholder": "Placeholder text",
    "enum": ["value1", "value2"]  // Opsiyonel: Enum değerleri
  }
}
```

**Örnek Input Schema:**
```json
{
  "api_key": {
    "type": "string",
    "required": true,
    "description": "API key for authentication"
  },
  "timeout": {
    "type": "integer",
    "required": false,
    "default": 30,
    "description": "Timeout in seconds"
  },
  "method": {
    "type": "string",
    "required": true,
    "enum": ["GET", "POST", "PUT", "DELETE"],
    "description": "HTTP method"
  }
}
```

**Type Mapping (Frontend için):**
- `string` → `text`
- `number`, `integer`, `float` → `number`
- `boolean` → `checkbox`
- `array`, `object` → `textarea`
- `email` → `email`
- `url` → `url`
- `password` → `password`
- `enum` varsa → `select`

### Output Schema Formatı

Output schema, script'in döndüreceği veri yapısını tanımlar. Bu şema execution sonuçlarını anlamak için kullanılır.

**Format:**
```json
{
  "output_field": {
    "type": "string|number|boolean|array|object",
    "description": "Output field description"
  }
}
```

**Örnek Output Schema:**
```json
{
  "status": {
    "type": "string",
    "description": "Processing status"
  },
  "data": {
    "type": "object",
    "description": "Processed data"
  },
  "count": {
    "type": "integer",
    "description": "Number of processed items"
  }
}
```

### Şema Validasyonu

Node oluşturulurken veya güncellenirken:

1. **Required Field Kontrolü**: `required: true` olan parametreler mutlaka sağlanmalı
2. **Type Kontrolü**: Parametre değerleri şemada belirtilen tipe uygun olmalı
3. **Enum Kontrolü**: `enum` tanımlıysa, değer enum listesinde olmalı
4. **Schema Uyumluluğu**: `input_params` içindeki tüm parametreler `input_schema`'da tanımlı olmalı

**Hata Örnekleri:**
- `Required parameter 'api_key' is missing`
- `Parameter 'timeout' must be a number`
- `Parameter 'method' must be one of ['GET', 'POST', 'PUT', 'DELETE'], got 'PATCH'`
- `Parameter 'unknown_param' is not defined in script's input_schema`

---

## Onay Workflow'u

### Custom Script Onay Durumları

1. **PENDING**: Script oluşturulduğunda otomatik olarak PENDING durumuna gelir
2. **APPROVED**: Admin tarafından onaylandığında APPROVED olur
3. **REJECTED**: Admin tarafından reddedildiğinde REJECTED olur

### Onay İşlemleri

**Approve Script:**
- **Endpoint**: `POST /frontend/workspaces/{workspace_id}/scripts/{script_id}/approve`
- **Gereksinim**: Admin authentication
- **Request Body**: `{"review_notes": "string (optional)"}`
- **Sonuç**: Script APPROVED durumuna geçer

**Reject Script:**
- **Endpoint**: `POST /frontend/workspaces/{workspace_id}/scripts/{script_id}/reject`
- **Gereksinim**: Admin authentication
- **Request Body**: `{"review_notes": "string (required)"}` - Red gerekçesi zorunludur
- **Sonuç**: Script REJECTED durumuna geçer

**Reset Approval Status:**
- **Endpoint**: `POST /frontend/workspaces/{workspace_id}/scripts/{script_id}/reset-approval`
- **Gereksinim**: Admin authentication
- **Sonuç**: Script PENDING durumuna geri döner

### Onay Durumunun Kullanımı

- **PENDING Scripts**: Node'larda kullanılamaz
- **APPROVED Scripts**: Node'larda kullanılabilir
- **REJECTED Scripts**: Node'larda kullanılamaz

---

## Önemli Kısıtlamalar

### 1. Script İçeriği Değiştirilemez

**Kritik Kural**: Script oluşturulduktan sonra `content` değiştirilemez. Bu güvenlik nedeniyle yapılmıştır.

**Çözüm**: Script içeriğini değiştirmek istiyorsanız:
1. Yeni bir script oluşturun
2. Eski script'i silin (eğer kullanılmıyorsa)
3. Node'lardaki script referanslarını güncelleyin

**Güncellenebilen Alanlar:**
- `description`
- `tags`
- `documentation_url`

### 2. Workspace Script Limitleri

Her workspace'in bir `custom_script_limit` değeri vardır. Bu limit aşıldığında yeni script oluşturulamaz.

**Hata Mesajı:**
```
Custom script limit reached. Maximum: {limit}
```

### 3. Script İsmi Benzersizliği

Script ismi workspace içinde benzersiz olmalıdır.

**Hata Mesajı:**
```
Resource already exists: CustomScript with id '{name}'
```

### 4. Script Dosya Yapısı

Script içeriği şu yapıda olmalıdır:

```python
def module():
    """
    Script modülü döndüren fonksiyon.
    Bu fonksiyon bir sınıf instance'ı döndürmelidir.
    """
    class YourScriptClass:
        def run(self, params):
            """
            Script'in ana çalışma fonksiyonu.
            
            Args:
                params: Dict[str, Any] - Script parametreleri (input_params'tan gelir)
            
            Returns:
                Dict[str, Any] - Script çıktısı (output_schema'ya uygun olmalı)
            """
            # Script logic burada
            return {
                "result": "success",
                "data": params.get("input_data")
            }
    
    return YourScriptClass()
```

**Zorunlu Yapı:**
- `module()` fonksiyonu olmalı
- `module()` bir sınıf instance'ı döndürmeli
- Dönen sınıfın `run(params)` metodu olmalı
- `run()` metodu bir dictionary döndürmeli

---

## Best Practices

### 1. Şema Tasarımı

- **Açıklayıcı İsimler**: Parametre isimleri açıklayıcı olmalı
- **Type Safety**: Doğru type'ları kullanın (string, number, boolean, vs.)
- **Required Fields**: Sadece gerçekten zorunlu parametreleri `required: true` yapın
- **Default Values**: Mümkün olduğunca default değerler sağlayın
- **Descriptions**: Her parametre için açıklama ekleyin

### 2. Script İçeriği

- **Error Handling**: Script içinde try-except blokları kullanın
- **Input Validation**: Script içinde de input validation yapın
- **Return Format**: Her zaman dictionary döndürün
- **Error Messages**: Hata durumlarında açıklayıcı mesajlar döndürün

**Örnek Script:**
```python
def module():
    class DataProcessor:
        def run(self, params):
            try:
                data = params.get('data')
                if not data:
                    return {
                        "status": "error",
                        "message": "Data parameter is required"
                    }
                
                # Processing logic
                result = process_data(data)
                
                return {
                    "status": "success",
                    "result": result
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
    
    return DataProcessor()
```

### 3. Required Packages

Script'in ihtiyaç duyduğu Python paketlerini `required_packages` listesine ekleyin:

```json
{
  "required_packages": ["pandas", "numpy", "requests"]
}
```

### 4. Documentation

- **Script Description**: Script'in ne yaptığını açıklayın
- **Documentation URL**: Daha detaylı dökümantasyon için URL ekleyin
- **Tags**: Script'i kategorize etmek için tag'ler kullanın

### 5. Test Status

Script'ler test edilebilir ve test durumu takip edilir:

- **UNTESTED**: Henüz test edilmemiş
- **PASSED**: Test başarılı
- **FAILED**: Test başarısız
- **SKIPPED**: Test atlandı

Test durumu script'in güvenilirliğini gösterir.

---

## Özet

1. **Script Türü Seçimi**: Global (tüm workspace'ler) veya Custom (workspace-specific)
2. **Şema Tasarımı**: Input ve output şemalarını doğru tasarlayın
3. **Onay Süreci**: Custom script'ler için onay bekleyin
4. **İçerik Değişikliği**: Script içeriği değiştirilemez, yeni script oluşturun
5. **Limit Kontrolü**: Workspace script limitlerini kontrol edin
6. **Best Practices**: Şema tasarımı, error handling, documentation

