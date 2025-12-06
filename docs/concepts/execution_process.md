# Execution Süreci

Bu dokümantasyon, MiniFlow Enterprise'da execution'ların nasıl başlatıldığını, işlendiğini ve tamamlandığını detaylı olarak açıklar.

## İçindekiler

1. [Execution Genel Bakış](#execution-genel-bakış)
2. [Execution Başlatma](#execution-başlatma)
3. [Execution Input Oluşturma](#execution-input-oluşturma)
4. [Execution İşleme Süreci](#execution-işleme-süreci)
5. [Execution Output İşleme](#execution-output-işleme)
6. [Execution Sonlandırma](#execution-sonlandırma)
7. [Execution Durumları](#execution-durumları)
8. [Dependency Yönetimi](#dependency-yönetimi)

---

## Execution Genel Bakış

Execution, bir workflow'un çalıştırılmasıdır. Bir execution şunları içerir:

- **Execution**: Ana execution kaydı
- **ExecutionInput**: Her node için oluşturulan input kayıtları
- **ExecutionOutput**: Her node'un çalıştırılması sonucu oluşan output kayıtları

**Execution Lifecycle:**
```
PENDING → RUNNING → COMPLETED/FAILED/CANCELLED/TIMEOUT
```

---

## Execution Başlatma

### Başlatma Yöntemleri

Execution iki şekilde başlatılabilir:

#### 1. Trigger ile Başlatma (API)

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/executions/test` (Admin only)

**Süreç:**
1. Trigger kontrolü: Trigger var mı, aktif mi?
2. Input mapping validation: `trigger_data` trigger'ın `input_mapping`'ine göre validate edilir
3. Execution oluşturulur: `trigger_id` ile
4. ExecutionInput'lar oluşturulur: Workflow'un tüm node'ları için

**Kod:**
```python
# ExecutionManagementService.start_execution_by_trigger()
1. Trigger getirilir ve is_enabled kontrol edilir
2. trigger.input_mapping'e göre trigger_data validate edilir
3. Execution oluşturulur (trigger_id ile)
4. _create_execution_inputs() çağrılır
```

#### 2. Workflow ile Başlatma (UI Test)

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/executions/test`

**Süreç:**
1. Herhangi bir kontrol yapılmaz (test amaçlı)
2. Execution oluşturulur: `trigger_id = None`
3. ExecutionInput'lar oluşturulur: Workflow'un tüm node'ları için

**Kod:**
```python
# ExecutionManagementService.start_execution_by_workflow()
1. Execution oluşturulur (trigger_id = None)
2. _create_execution_inputs() çağrılır
```

**Önemli Fark:**
- Trigger ile başlatmada trigger aktif mi kontrol edilir
- Workflow ile başlatmada hiçbir kontrol yapılmaz (test için)

---

## Execution Input Oluşturma

### ExecutionInput Oluşturma Süreci

**Method:** `ExecutionManagementService._create_execution_inputs()`

**Süreç:**

1. **Node'ları Getir**: Workflow'un tüm node'ları getirilir
2. **Edge'leri Getir**: Workflow'un tüm edge'leri getirilir
3. **Dependency Map Oluştur**: Her node'un kaç dependency'si var hesaplanır
   ```python
   dependency_map = {
       "node_b_id": ["node_a_id"],  # Node B, Node A'yı bekliyor
       "node_c_id": ["node_b_id"],  # Node C, Node B'yi bekliyor
   }
   ```
4. **Script'leri Getir**: Global ve custom script'ler batch olarak getirilir
5. **Her Node İçin ExecutionInput Oluştur**:
   - `dependency_count`: O node'a gelen edge sayısı
   - `priority`: Workflow'un priority değeri
   - `max_retries`: Node'un max_retries değeri
   - `timeout_seconds`: Node'un timeout_seconds değeri
   - `params`: Node'un input_params'ından çıkarılan parametreler
   - `script_path`: Script'in dosya yolu

**ExecutionInput Yapısı:**
```python
{
    "execution_id": "EXC123...",
    "workflow_id": "WFL123...",
    "workspace_id": "WSP123...",
    "node_id": "NOD123...",
    "dependency_count": 2,  # Kaç node'un tamamlanmasını bekliyor
    "priority": 1,
    "max_retries": 3,
    "timeout_seconds": 300,
    "node_name": "Process Data",
    "params": {
        "api_key": {"type": "string", "value": "xxx"},
        "timeout": {"type": "integer", "value": 30}
    },
    "script_name": "data_processor",
    "script_path": "/path/to/script.py"
}
```

**Önemli:**
- `dependency_count = 0` olan node'lar hemen çalıştırılabilir
- `dependency_count > 0` olan node'lar, dependency'leri tamamlanana kadar bekler

---

## Execution İşleme Süreci

### ExecutionInputHandler

ExecutionInputHandler, hazır execution input'ları alır, context oluşturur ve engine'e gönderir.

**Lifecycle:**

1. **Main Loop**: Sürekli çalışan döngü
   - `get_ready_execution_inputs()`: Hazır input'ları getirir
   - `_process_tasks()`: Task'ları işler
   - Adaptive polling: İş yüküne göre polling interval ayarlanır

2. **Ready Execution Inputs**: 
   - `dependency_count = 0` olan input'lar hazırdır
   - Veya tüm dependency'leri tamamlanmış input'lar hazırdır

3. **Context Oluşturma**:
   - Her execution input için context oluşturulur
   - Parameter resolution yapılır (variable, credential, vs. referansları çözülür)
   - Context engine'e gönderilecek formata hazırlanır

4. **Engine'e Gönderme**:
   - Payload'lar engine'e gönderilir
   - Başarılı gönderimden sonra ExecutionInput'lar silinir

### Context Oluşturma

**Method:** `SchedulerForInputHandler.create_execution_context()`

**Süreç:**

1. **Parameter Resolution**:
   - `params` içindeki referanslar parse edilir ve gruplandırılır:
     - Format: `${type:id_or_value.path}`
     - `value`: `${value:ENV-456}` - Variable referansları
     - `credential`: `${credential:CRD-123.api_key}` - Credential referansları
     - `node`: `${node:NOD-789.result.data}` - Önceki node output referansları
     - `trigger`: `${trigger:data.user.id}` - Trigger data referansları
     - `database`: `${database:DBS-111.host}` - Database connection referansları
     - `file`: `${file:FLE-222.content}` - File content referansları
     - `static`: `${static:30}` - Statik değerler

2. **Reference Resolution**:
   - Her grup için referanslar çözülür:
     - `value`: Variable'dan değer alınır (şifreli ise çözülür, tip dönüşümü yapılır)
     - `credential`: Credential'dan değer alınır (şifreli ise çözülür, nested path desteklenir)
     - `node`: ExecutionOutput.result_data'dan değer alınır (nested path desteklenir)
     - `trigger`: Execution.trigger_data'dan değer alınır (nested path desteklenir)
     - `database`: Database connection string'den değer alınır
     - `file`: File content'ten değer alınır
     - `static`: Statik değer tip dönüşümü yapılır (expected_type'a göre)

3. **Context Oluşturma**:
   ```python
   context = {
       "execution_id": "EXC123...",
       "workspace_id": "WSP123...",
       "workflow_id": "WFL123...",
       "node_id": "NOD123...",
       "script_path": "/path/to/script.py",
       "params": {
           "api_key": "resolved_value",
           "timeout": 30
       },
       "max_retries": 3,
       "timeout_seconds": 300
   }
   ```

### Engine'e Gönderme

**Payload Formatı:**
```python
{
    "execution_id": "EXC123...",
    "node_id": "NOD123...",
    "process_type": "python",
    "script_path": "/path/to/script.py",
    "params": {
        "api_key": "xxx",
        "timeout": 30
    }
}
```

**Engine İşleme:**
1. Script dosyası yüklenir
2. `module()` fonksiyonu çağrılır
3. `run(params)` metodu çağrılır
4. Sonuç ExecutionOutput olarak kaydedilir

---

## Execution Output İşleme

### ExecutionOutput Oluşturma

Engine script'i çalıştırdıktan sonra sonuç ExecutionOutput olarak kaydedilir.

**ExecutionOutput Yapısı:**
```python
{
    "execution_id": "EXC123...",
    "node_id": "NOD123...",
    "status": "SUCCESS|FAILED",
    "result_data": {
        "output_field": "value"
    },
    "duration": 2.5,  # Saniye cinsinden
    "error_message": None,  # Hata varsa
    "error_details": None  # Hata detayları varsa
}
```

### ExecutionOutputHandler

ExecutionOutputHandler, engine'den gelen execution result'ları alır ve işler.

**Lifecycle:**

1. **Main Loop**: Sürekli çalışan döngü
   - `get_execution_results()`: Engine'den result'ları getirir
   - `_process_results()`: Result'ları işler
   - Adaptive polling: İş yüküne göre polling interval ayarlanır

2. **Result İşleme**:
   - Her result için ExecutionOutput kaydedilir
   - Dependency'leri tamamlanan node'ların ExecutionInput'ları "ready" yapılır
   - Execution durumu güncellenir

### Dependency Yönetimi

Bir node'un ExecutionOutput'u oluşturulduğunda:

1. **Dependency Kontrolü**: Bu node'un output'unu bekleyen node'lar bulunur
2. **Dependency Count Güncelleme**: Bekleyen node'ların `dependency_count` değeri azaltılır
3. **Ready Kontrolü**: `dependency_count = 0` olan node'lar "ready" yapılır

**Örnek:**
```
Node A → Node B → Node C

1. Node A tamamlandı → Node B'nin dependency_count: 1 → 0 (ready)
2. Node B tamamlandı → Node C'nin dependency_count: 1 → 0 (ready)
3. Node C çalıştırılabilir
```

---

## Execution Sonlandırma

### Execution Durumları

Execution'lar şu durumlarda sonlanır:

1. **COMPLETED**: Tüm node'lar başarıyla tamamlandı
2. **FAILED**: Bir veya daha fazla node başarısız oldu
3. **CANCELLED**: Execution manuel olarak iptal edildi
4. **TIMEOUT**: Execution timeout'a uğradı

### End Execution

**Method:** `ExecutionManagementService.end_execution()`

**Süreç:**

1. **Sonuçları Topla**: `_collect_execution_results()`
   - Tüm ExecutionOutput'lar toplanır
   - Bekleyen ExecutionInput'lar CANCELLED olarak işaretlenir

2. **Cleanup**:
   - ExecutionInput'lar silinir
   - ExecutionOutput'lar silinir

3. **Execution Güncelleme**:
   - `status`: Final durum (COMPLETED, FAILED, etc.)
   - `ended_at`: Sonlandırma zamanı
   - `duration`: Süre (ended_at - started_at)
   - `results`: Toplanan sonuçlar

**Results Formatı:**
```python
{
    "node_id_1": {
        "status": "SUCCESS",
        "result_data": {...},
        "duration": 2.5,
        "error_message": None,
        "error_details": None
    },
    "node_id_2": {
        "status": "FAILED",
        "result_data": None,
        "duration": 1.2,
        "error_message": "Script execution failed",
        "error_details": {...}
    }
}
```

---

## Execution Durumları

### Durum Türleri

1. **PENDING**: Execution başlatıldı, henüz işlenmeye başlamadı
2. **RUNNING**: Execution işleniyor (en az bir node çalışıyor)
3. **COMPLETED**: Tüm node'lar başarıyla tamamlandı
4. **FAILED**: Bir veya daha fazla node başarısız oldu
5. **CANCELLED**: Execution manuel olarak iptal edildi
6. **TIMEOUT**: Execution timeout'a uğradı

### Durum Geçişleri

```
PENDING → RUNNING (ilk node çalışmaya başladığında)
RUNNING → COMPLETED (tüm node'lar başarıyla tamamlandığında)
RUNNING → FAILED (bir node başarısız olduğunda)
RUNNING → CANCELLED (manuel iptal)
RUNNING → TIMEOUT (timeout)
```

---

## Dependency Yönetimi

### Dependency Graph

Edge'ler dependency graph oluşturur:

```
Node A → Node B → Node C
  ↓
Node D
```

**Dependency Map:**
```python
{
    "node_b_id": ["node_a_id"],      # Node B, Node A'yı bekliyor
    "node_c_id": ["node_b_id"],      # Node C, Node B'yi bekliyor
    "node_d_id": ["node_a_id"]       # Node D, Node A'yı bekliyor
}
```

### ExecutionInput Dependency Count

Her ExecutionInput için `dependency_count` hesaplanır:

- **dependency_count = 0**: Node'un dependency'si yok, hemen çalıştırılabilir
- **dependency_count > 0**: Node'un dependency'leri var, beklemeli

**Örnek:**
- Node A: `dependency_count = 0` → Hemen çalıştırılabilir
- Node B: `dependency_count = 1` → Node A tamamlanana kadar bekler
- Node C: `dependency_count = 1` → Node B tamamlanana kadar bekler
- Node D: `dependency_count = 1` → Node A tamamlanana kadar bekler

### Dependency Resolution

Bir node tamamlandığında:

1. **Output Kaydedilir**: ExecutionOutput oluşturulur
2. **Bekleyen Node'lar Bulunur**: Bu node'un output'unu bekleyen node'lar
3. **Dependency Count Güncellenir**: Bekleyen node'ların `dependency_count` değeri azaltılır
4. **Ready Kontrolü**: `dependency_count = 0` olan node'lar "ready" yapılır

**Kod:**
```python
# Node A tamamlandı
# Node B ve Node D'nin dependency_count'u azaltılır
# dependency_count = 0 olan node'lar ready yapılır
```

---

## Execution Akış Şeması

```
1. Execution Başlatma
   ├─ Trigger ile (API)
   │  ├─ Trigger kontrolü
   │  └─ Input mapping validation
   └─ Workflow ile (UI Test)
      └─ Kontrol yok

2. ExecutionInput Oluşturma
   ├─ Node'lar getirilir
   ├─ Edge'ler getirilir
   ├─ Dependency map oluşturulur
   ├─ Script'ler getirilir
   └─ Her node için ExecutionInput oluşturulur

3. Execution İşleme
   ├─ ExecutionInputHandler
   │  ├─ Ready input'ları getir
   │  ├─ Context oluştur
   │  │  ├─ Parameter resolution
   │  │  └─ Reference resolution
   │  └─ Engine'e gönder
   └─ Engine
      ├─ Script yükle
      ├─ module() çağır
      └─ run(params) çağır

4. ExecutionOutput İşleme
   ├─ ExecutionOutputHandler
   │  ├─ Result'ları al
   │  ├─ ExecutionOutput kaydet
   │  └─ Dependency'leri güncelle
   └─ Dependency Resolution
      ├─ Bekleyen node'ları bul
      ├─ dependency_count azalt
      └─ Ready node'ları işaretle

5. Execution Sonlandırma
   ├─ Tüm node'lar tamamlandı
   ├─ Sonuçları topla
   ├─ Cleanup (ExecutionInput/Output sil)
   └─ Execution durumunu güncelle
```

---

## Özet

1. **Execution Başlatma**: Trigger veya Workflow ile başlatılır
2. **ExecutionInput Oluşturma**: Her node için input oluşturulur, dependency_count hesaplanır
3. **Execution İşleme**: Ready input'lar context'e dönüştürülür, engine'e gönderilir
4. **ExecutionOutput İşleme**: Engine'den gelen sonuçlar kaydedilir, dependency'ler güncellenir
5. **Execution Sonlandırma**: Tüm node'lar tamamlandığında execution sonlandırılır

