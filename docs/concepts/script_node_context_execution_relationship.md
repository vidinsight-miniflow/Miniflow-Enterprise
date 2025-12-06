# Script → Node → Context → Execution İlişkisi

Bu dokümantasyon, MiniFlow Enterprise'da script'lerin node'lara, node'ların context'lere ve context'lerin execution'lara nasıl dönüştüğünü detaylı olarak açıklar.

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Script Katmanı](#script-katmanı)
3. [Node Katmanı](#node-katmanı)
4. [Context Katmanı](#context-katmanı)
5. [Execution Katmanı](#execution-katmanı)
6. [Veri Akışı](#veri-akışı)
7. [Dönüşüm Süreçleri](#dönüşüm-süreçleri)
8. [Örnek Senaryo](#örnek-senaryo)

---

## Genel Bakış

MiniFlow Enterprise'da execution süreci şu katmanlardan oluşur:

```
Script (Kod) 
    ↓
Node (Yapılandırma)
    ↓
ExecutionInput (Hazırlık)
    ↓
Context (Çözümleme)
    ↓
Execution (Çalıştırma)
```

**Her katmanın rolü:**
- **Script**: Python kod dosyası, iş mantığını içerir
- **Node**: Script'i workflow'a bağlar, parametreleri tanımlar
- **ExecutionInput**: Execution için node'un anlık görüntüsünü oluşturur
- **Context**: ExecutionInput'tan engine'e gönderilecek formata dönüştürür
- **Execution**: Context'i engine'e gönderir ve sonuçları toplar

---

## Script Katmanı

### Script Yapısı

Script, Python kod dosyasıdır ve iki türde olabilir:

1. **Global Script** (`Script` modeli)
   - Tüm workspace'lerden erişilebilir
   - Admin tarafından yönetilir
   - `file_path`: Script dosyasının disk yolu

2. **Custom Script** (`CustomScript` modeli)
   - Sadece oluşturulduğu workspace'de kullanılabilir
   - Workspace üyeleri tarafından oluşturulur
   - Onay workflow'u vardır (PENDING → APPROVED)
   - `file_path`: Script dosyasının disk yolu

### Script Özellikleri

**Script Model Alanları:**
```python
{
    "id": "SCR123...",
    "name": "data_processor",
    "content": "def module():\n    class Processor:\n        ...",
    "file_path": "/workspace/scripts/data_processor.py",
    "input_schema": {
        "api_key": {
            "type": "string",
            "required": true,
            "description": "API key"
        },
        "timeout": {
            "type": "integer",
            "required": false,
            "default": 30
        }
    },
    "output_schema": {
        "result": {
            "type": "object",
            "description": "Processing result"
        }
    }
}
```

**Script Zorunlu Yapısı:**
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
                params: Dict[str, Any] - Script parametreleri
            
            Returns:
                Dict[str, Any] - Script çıktısı
            """
            return {"result": "success"}
    
    return YourScriptClass()
```

---

## Node Katmanı

### Node Yapısı

Node, bir workflow içindeki bir adımdır ve bir script ile bağlantılıdır.

**Node Model Alanları:**
```python
{
    "id": "NOD123...",
    "workflow_id": "WFL123...",
    "name": "Process Data",
    "script_id": "SCR123...",  # VEYA
    "custom_script_id": "CSC123...",  # XOR: Sadece biri
    "input_params": {
        "api_key": {
            "type": "string",
            "value": "${credential:CRD-123.api_key}",  # Referans
            "required": true
        },
        "timeout": {
            "type": "integer",
            "value": 30,  # Statik değer
            "default_value": 30
        }
    },
    "output_params": {},
    "max_retries": 3,
    "timeout_seconds": 300,
    "meta_data": {}
}
```

### Script-Node Bağlantısı

**Kurallar:**
1. **XOR Kuralı**: Ya `script_id` ya da `custom_script_id` verilmeli (ikisi birden olamaz)
2. **Workspace Uyumu**: Custom script seçildiğinde, script'in workspace_id'si workflow'un workspace_id'si ile aynı olmalı
3. **Input Params Validasyonu**: Node'un `input_params`'ı script'in `input_schema`'sına göre validate edilir

**Node Oluşturma Süreci:**
```python
# NodeService.create_node()
1. Script kontrolü: script_id veya custom_script_id var mı?
2. Script getirilir: Global veya Custom script
3. Workspace uyumu kontrol edilir (custom script için)
4. input_params validate edilir: script'in input_schema'sına göre
5. Node oluşturulur: script_id/custom_script_id ile bağlantı kurulur
```

### Input Params Formatı

Node'da saklanan `input_params` formatı:

```json
{
  "param_name": {
    "type": "string|number|boolean|...",
    "value": "actual_value | {{reference}}",
    "default_value": "default",
    "required": true|false,
    "description": "Parameter description"
  }
}
```

**Değer Türleri:**
- **Statik Değer**: `"value": 30`
- **Referans**: `"value": "${credential:CRD-123.api_key}"` veya `"value": "${value:ENV-456}"` veya `"value": "${node:NOD-789.result.data}"`

---

## Context Katmanı

### ExecutionInput Yapısı

Execution başlatıldığında, her node için bir `ExecutionInput` oluşturulur.

**ExecutionInput Model Alanları:**
```python
{
    "id": "EXI123...",
    "execution_id": "EXC123...",
    "workflow_id": "WFL123...",
    "workspace_id": "WSP123...",
    "node_id": "NOD123...",
    
    # Zamanlama
    "dependency_count": 2,  # Kaç node'un tamamlanmasını bekliyor
    "priority": 1,
    
    # Execution ayarları (Node'dan kopyalanır)
    "max_retries": 3,
    "timeout_seconds": 300,
    
    # Anlık görüntü (Node'dan kopyalanır)
    "node_name": "Process Data",
    "params": {
        "api_key": {
            "type": "string",
            "value": "${credential:CRD-123.api_key}"
        },
        "timeout": {
            "type": "integer",
            "value": 30
        }
    },
    "script_name": "data_processor",
    "script_path": "/workspace/scripts/data_processor.py"
}
```

### ExecutionInput Oluşturma

**Süreç:** `ExecutionManagementService._create_execution_inputs()`

```python
1. Node'lar getirilir: Workflow'un tüm node'ları
2. Edge'ler getirilir: Dependency graph oluşturmak için
3. Dependency map oluşturulur: Her node'un dependency_count'u hesaplanır
4. Script'ler getirilir: Global ve custom script'ler batch olarak
5. Her node için ExecutionInput oluşturulur:
   - Node'un input_params'ı kopyalanır
   - Script'in file_path'i kopyalanır
   - Node'un max_retries ve timeout_seconds değerleri kopyalanır
   - dependency_count hesaplanır
```

**Önemli:** ExecutionInput, node'un anlık görüntüsüdür. Node silinse bile ExecutionInput kalır.

### Context Oluşturma

**Süreç:** `SchedulerForInputHandler.create_execution_context()`

ExecutionInput'tan Context oluşturulurken:

1. **Reference Detection**: Her parametre değeri kontrol edilir
   - Format kontrolü: `${` ile başlayıp `}` ile bitiyor mu?
   - `:` karakteri var mı?
   - Geçerli referans tipleri: `static`, `trigger`, `node`, `value`, `credential`, `database`, `file`

2. **Reference Parsing**: Referans string'i parse edilir
   - Format: `${type:id_or_value.path}`
   - Örnek: `${credential:CRD-123.api_key}` → `type=credential`, `id=CRD-123`, `value_path=api_key`
   - Örnek: `${node:NOD-789.result.data}` → `type=node`, `id=NOD-789`, `value_path=result.data`
   - Örnek: `${trigger:data.user.id}` → `type=trigger`, `value_path=data.user.id` (id yok)
   - Örnek: `${static:30}` → `type=static`, `id_or_value=30`

3. **Parameter Resolution**: Referanslar gruplandırılır
   ```python
   groups = {
       "value": [
           {"type": "value", "id": "ENV-456", "param_name": "token", "expected_type": "string"}
       ],
       "credential": [
           {"type": "credential", "id": "CRD-123", "value_path": "api_key", "param_name": "api_key", "expected_type": "string"}
       ],
       "node": [
           {"type": "node", "id": "NOD-789", "value_path": "result.data", "param_name": "previous_result", "expected_type": "object"}
       ],
       "trigger": [
           {"type": "trigger", "value_path": "data.user.id", "param_name": "user_id", "expected_type": "string"}
       ],
       "static": [
           {"type": "static", "id_or_value": "30", "param_name": "timeout", "expected_type": "integer"}
       ]
   }
   ```

4. **Reference Resolution**: Her grup için referanslar çözülür
   - Her referans tipi için özel resolver metodu çağrılır:
     - `RefrenceResolver.get_static_data()` - Statik değerler için
     - `RefrenceResolver.get_trigger_data()` - Trigger data için
     - `RefrenceResolver.get_executed_node_data()` - Node output'ları için
     - `RefrenceResolver.get_variable_data()` - Variable'lar için
     - `RefrenceResolver.get_credential_data()` - Credential'lar için
     - `RefrenceResolver.get_database_data()` - Database connection'lar için
     - `RefrenceResolver.get_file_data()` - File'lar için
   - Her resolver:
     1. Nested path'i parse eder (`_resolve_nested_reference`)
     2. Context'ten değeri çıkarır (`_get_value_from_context`)
     3. Tip dönüşümü yapar (`_convert_to_type`)
   
   ```python
   resolved_params = {
       "api_key": "actual_secret_value",  # Credential'dan çözüldü
       "timeout": 30,  # Statik değer (integer'a dönüştürüldü)
       "token": "actual_token_value",  # Variable'dan çözüldü
       "previous_result": {"status": "success"}  # Node output'undan çözüldü
   }
   ```

5. **Context Oluşturma**: Engine'e gönderilecek format
   ```python
   context = {
       "execution_id": "EXC123...",
       "workspace_id": "WSP123...",
       "workflow_id": "WFL123...",
       "node_id": "NOD123...",
       "script_path": "/workspace/scripts/data_processor.py",
       "params": {
           "api_key": "actual_secret_value",
           "timeout": 30
       },
       "max_retries": 3,
       "timeout_seconds": 300
   }
   ```

---

## Execution Katmanı

### Execution Yapısı

Execution, bir workflow'un çalıştırılmasıdır.

**Execution Model Alanları:**
```python
{
    "id": "EXC123...",
    "workspace_id": "WSP123...",
    "workflow_id": "WFL123...",
    "trigger_id": "TRG123...",  # Opsiyonel
    "status": "PENDING|RUNNING|COMPLETED|FAILED|CANCELLED|TIMEOUT",
    "started_at": "2024-01-01T00:00:00Z",
    "ended_at": "2024-01-01T00:05:00Z",
    "duration": 300.0,
    "trigger_data": {...},
    "results": {
        "NOD123": {
            "status": "SUCCESS",
            "result_data": {...},
            "duration": 2.5
        }
    }
}
```

### ExecutionInput → Context → Engine

**Akış:**

1. **Ready ExecutionInput'lar**: `dependency_count = 0` olan ExecutionInput'lar
2. **Context Oluşturma**: Her ExecutionInput için context oluşturulur
3. **Engine'e Gönderme**: Context'ler engine'e gönderilir
4. **Script Çalıştırma**: Engine script'i yükler ve çalıştırır
5. **ExecutionOutput**: Sonuç ExecutionOutput olarak kaydedilir

---

## Veri Akışı

### Tam Veri Akışı

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SCRIPT (Kaynak)                                          │
│    - content: Python kodu                                    │
│    - input_schema: Parametre tanımları                       │
│    - output_schema: Çıktı tanımları                          │
│    - file_path: Disk yolu                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. NODE (Yapılandırma)                                       │
│    - script_id veya custom_script_id: Script bağlantısı      │
│    - input_params: Parametre değerleri (referanslar dahil)   │
│    - max_retries, timeout_seconds: Execution ayarları        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (Execution başlatıldığında)
┌─────────────────────────────────────────────────────────────┐
│ 3. EXECUTIONINPUT (Anlık Görüntü)                           │
│    - params: Node'un input_params'ı kopyalanır              │
│    - script_path: Script'in file_path'i kopyalanır           │
│    - dependency_count: Dependency sayısı                     │
│    - max_retries, timeout_seconds: Node'dan kopyalanır       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (Ready olduğunda)
┌─────────────────────────────────────────────────────────────┐
│ 4. CONTEXT (Çözülmüş)                                       │
│    - script_path: ExecutionInput'tan                         │
│    - params: Referanslar çözülmüş değerler                  │
│    - max_retries, timeout_seconds: ExecutionInput'tan        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (Engine'e gönderilir)
┌─────────────────────────────────────────────────────────────┐
│ 5. ENGINE (Çalıştırma)                                       │
│    - Script dosyası yüklenir (script_path'ten)              │
│    - module() çağrılır                                        │
│    - run(params) çağrılır (context'ten params)               │
│    - Sonuç döndürülür                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. EXECUTIONOUTPUT (Sonuç)                                   │
│    - result_data: Script'in döndürdüğü veri                  │
│    - status: SUCCESS veya FAILED                             │
│    - duration: Çalıştırma süresi                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dönüşüm Süreçleri

### 1. Script → Node Dönüşümü

**Node Oluşturulurken:**

```python
# NodeService.create_node()
script = get_script(script_id)  # Script getirilir

# Input params validate edilir
validated_params = validate_and_convert_frontend_params(
    frontend_params=input_params,
    script_input_schema=script.input_schema
)

# Node oluşturulur
node = create_node(
    script_id=script_id,
    input_params=validated_params,
    max_retries=3,
    timeout_seconds=300
)
```

**Dönüşüm:**
- Script'in `input_schema`'sı → Node'un `input_params` validasyonu
- Script'in `file_path`'i → Node'da saklanmaz (execution sırasında script'ten alınır)

### 2. Node → ExecutionInput Dönüşümü

**Execution Başlatıldığında:**

```python
# ExecutionManagementService._create_execution_inputs()
for node in nodes:
    script = get_script(node.script_id or node.custom_script_id)
    
    # Node'dan ExecutionInput'a kopyalama
    execution_input = create_execution_input(
        execution_id=execution_id,
        node_id=node.id,
        params=node.input_params,  # Kopyalanır
        script_path=script.file_path,  # Script'ten alınır
        script_name=script.name,  # Script'ten alınır
        max_retries=node.max_retries,  # Kopyalanır
        timeout_seconds=node.timeout_seconds,  # Kopyalanır
        dependency_count=calculate_dependency_count(node)  # Hesaplanır
    )
```

**Dönüşüm:**
- Node'un `input_params`'ı → ExecutionInput'un `params`'ı (kopyalanır)
- Script'in `file_path`'i → ExecutionInput'un `script_path`'i (kopyalanır)
- Node'un `max_retries` ve `timeout_seconds` → ExecutionInput'a kopyalanır

### 3. ExecutionInput → Context Dönüşümü

**Ready ExecutionInput İşlenirken:**

```python
# SchedulerForInputHandler.create_execution_context()
execution_input = get_execution_input(execution_input_id)

# Parameter resolution
groups = resolve_parameters(
    workspace_id=execution_input.workspace_id,
    execution_id=execution_input.execution_id,
    params=execution_input.params
)

# Reference resolution
resolved_params = resolve_references(groups, session)

# Context oluşturma
context = {
    "execution_id": execution_input.execution_id,
    "workspace_id": execution_input.workspace_id,
    "workflow_id": execution_input.workflow_id,
    "node_id": execution_input.node_id,
    "script_path": execution_input.script_path,  # Kopyalanır
    "params": resolved_params,  # Çözülmüş değerler
    "max_retries": execution_input.max_retries,  # Kopyalanır
    "timeout_seconds": execution_input.timeout_seconds  # Kopyalanır
}
```

**Dönüşüm:**
- ExecutionInput'un `params`'ı → Context'in `params`'ı (referanslar çözülür)
- ExecutionInput'un `script_path`'i → Context'in `script_path`'i (kopyalanır)
- ExecutionInput'un `max_retries` ve `timeout_seconds` → Context'e kopyalanır

### 4. Context → Engine Dönüşümü

**Engine'e Gönderilirken:**

```python
# ExecutionInputHandler._prepare_payloads()
payload = {
    "execution_id": context["execution_id"],
    "node_id": context["node_id"],
    "process_type": "python",
    "script_path": context["script_path"],  # Kopyalanır
    "params": context["params"]  # Kopyalanır
}
```

**Engine İşleme:**
```python
# Engine python_runner
1. Script dosyası yüklenir: script_path'ten
2. module() çağrılır: Script'ten
3. run(params) çağrılır: context'ten params ile
4. Sonuç döndürülür: ExecutionOutput olarak kaydedilir
```

---

## Örnek Senaryo

### Senaryo: Basit Data Processing Workflow

**1. Script Oluşturma:**

```python
# Script: data_processor.py
def module():
    class DataProcessor:
        def run(self, params):
            api_key = params.get("api_key")
            timeout = params.get("timeout", 30)
            
            # Processing logic
            result = process_data(api_key, timeout)
            
            return {
                "status": "success",
                "processed_count": result.count,
                "data": result.data
            }
    
    return DataProcessor()
```

**Script Model:**
```json
{
  "id": "SCR123",
  "name": "data_processor",
  "file_path": "/workspace/scripts/data_processor.py",
  "input_schema": {
    "api_key": {
      "type": "string",
      "required": true
    },
    "timeout": {
      "type": "integer",
      "required": false,
      "default": 30
    }
  }
}
```

**2. Node Oluşturma:**

```python
# NodeService.create_node()
node = create_node(
    workflow_id="WFL123",
    name="Process Data",
    script_id="SCR123",
    input_params={
        "api_key": {
            "type": "string",
            "value": "${credential:CRD-123.api_key}",  # Referans
            "required": true
        },
        "timeout": {
            "type": "integer",
            "value": 60,  # Statik değer
            "default_value": 30
        }
    },
    max_retries=3,
    timeout_seconds=300
)
```

**Node Model:**
```json
{
  "id": "NOD123",
  "workflow_id": "WFL123",
  "name": "Process Data",
  "script_id": "SCR123",
  "input_params": {
    "api_key": {
      "type": "string",
      "value": "${credential:CRD-123.api_key}",
      "required": true
    },
    "timeout": {
      "type": "integer",
      "value": 60,
      "default_value": 30
    }
  },
  "max_retries": 3,
  "timeout_seconds": 300
}
```

**3. Execution Başlatma:**

```python
# ExecutionManagementService.start_execution_by_workflow()
execution = create_execution(workflow_id="WFL123")
execution_input = create_execution_input(
    execution_id=execution.id,
    node_id="NOD123",
    params={
        "api_key": {
            "type": "string",
            "value": "${credential:CRD-123.api_key}"  # Node'dan kopyalandı
        },
        "timeout": {
            "type": "integer",
            "value": 60  # Node'dan kopyalandı
        }
    },
    script_path="/workspace/scripts/data_processor.py",  # Script'ten
    script_name="data_processor",  # Script'ten
    max_retries=3,  # Node'dan
    timeout_seconds=300  # Node'dan
)
```

**ExecutionInput Model:**
```json
{
  "id": "EXI123",
  "execution_id": "EXC123",
  "node_id": "NOD123",
  "params": {
    "api_key": {
      "type": "string",
      "value": "${credential:CRD-123.api_key}"
    },
    "timeout": {
      "type": "integer",
      "value": 60
    }
  },
  "script_path": "/workspace/scripts/data_processor.py",
  "script_name": "data_processor",
  "dependency_count": 0,
  "max_retries": 3,
  "timeout_seconds": 300
}
```

**4. Context Oluşturma:**

```python
# SchedulerForInputHandler.create_execution_context()
# Parameter resolution
groups = {
    "credential": [
        {"type": "credential", "id": "CRD-123", "value_path": "api_key", "param_name": "api_key", "expected_type": "string", "workspace_id": "WSP123", "execution_id": "EXC123"}
    ]
}

# Reference resolution
resolved_params = {
    "api_key": "actual_secret_key_12345",  # Credential'dan çözüldü
    "timeout": 60  # Statik değer
}

context = {
    "execution_id": "EXC123",
    "workspace_id": "WSP123",
    "workflow_id": "WFL123",
    "node_id": "NOD123",
    "script_path": "/workspace/scripts/data_processor.py",
    "params": {
        "api_key": "actual_secret_key_12345",
        "timeout": 60
    },
    "max_retries": 3,
    "timeout_seconds": 300
}
```

**5. Engine'e Gönderme:**

```python
# ExecutionInputHandler._prepare_payloads()
payload = {
    "execution_id": "EXC123",
    "node_id": "NOD123",
    "process_type": "python",
    "script_path": "/workspace/scripts/data_processor.py",
    "params": {
        "api_key": "actual_secret_key_12345",
        "timeout": 60
    }
}
```

**6. Engine İşleme:**

```python
# Engine python_runner
1. Script yüklenir: /workspace/scripts/data_processor.py
2. module() çağrılır → DataProcessor instance döner
3. run(params) çağrılır:
   params = {
       "api_key": "actual_secret_key_12345",
       "timeout": 60
   }
4. Sonuç döndürülür:
   {
       "status": "success",
       "processed_count": 100,
       "data": {...}
   }
```

**7. ExecutionOutput:**

```json
{
  "id": "EXO123",
  "execution_id": "EXC123",
  "node_id": "NOD123",
  "status": "SUCCESS",
  "result_data": {
    "status": "success",
    "processed_count": 100,
    "data": {...}
  },
  "duration": 2.5
}
```

---

## Reference Sistemi Detayları

### Reference Format

**Genel Format:** `${type:id_or_value.path}`

**Referans Tipleri:**

1. **Static**: `${static:value}`
   - Statik değerler için
   - Örnek: `${static:30}`, `${static:hello}`
   - Tip dönüşümü yapılır (expected_type'a göre)

2. **Trigger**: `${trigger:path}`
   - Execution.trigger_data'dan değer alır
   - Örnek: `${trigger:data.user.id}`, `${trigger:items[0].name}`
   - Nested path desteklenir (dot notation ve array index)

3. **Node**: `${node:node_id.path}`
   - Önceki node'un ExecutionOutput.result_data'sından değer alır
   - Örnek: `${node:NOD-123.result}`, `${node:NOD-123.data.items[0].name}`
   - Nested path desteklenir

4. **Value (Variable)**: `${value:variable_id}`
   - Workspace variable'ından değer alır
   - Örnek: `${value:ENV-456}`
   - Şifreli ise otomatik çözülür
   - Tip dönüşümü yapılır

5. **Credential**: `${credential:credential_id.path}`
   - Credential'dan değer alır
   - Örnek: `${credential:CRD-123.api_key}`, `${credential:CRD-123.data.token}`
   - Şifreli ise otomatik çözülür
   - Nested path desteklenir

6. **Database**: `${database:database_id.path}`
   - Database connection string'den değer alır
   - Örnek: `${database:DBS-111.host}`, `${database:DBS-111.port}`
   - Nested path desteklenir

7. **File**: `${file:file_id.path}`
   - File content'ten değer alır
   - Örnek: `${file:FLE-222.content}`, `${file:FLE-222.metadata.size}`
   - Nested path desteklenir

### Reference Resolution Süreci

**1. Reference Detection (`_is_reference`):**
```python
# Kontroller:
- Değer string mi?
- `${` ile başlıyor mu?
- `}` ile bitiyor mu?
- `:` karakteri var mı?
```

**2. Reference Parsing (`_parse_refrence`):**
```python
# Örnek: "${credential:CRD-123.api_key}"
content = "credential:CRD-123.api_key"  # ${ ve } kaldırıldı
ref_type, identifier_path = content.split(":", 1)
# ref_type = "credential"
# identifier_path = "CRD-123.api_key"

# Eğer "." varsa:
id, value_path = identifier_path.split(".", 1)
# id = "CRD-123"
# value_path = "api_key"
```

**3. Parameter Resolution (`resolve_parameters`):**
```python
# Her parametre için:
for param_name, param_data in params.items():
    param_value = param_data.get('value')
    expected_type = param_data.get('type')
    
    if _is_reference(param_value):
        reference_info = _parse_refrence(param_value, param_name, expected_type)
        reference_info['workspace_id'] = workspace_id
        reference_info['execution_id'] = execution_id
        groups[reference_info['type']].append(reference_info)
    else:
        # Statik değer
        groups['static'].append({...})
```

**4. Reference Resolution (`resolve_refrences`):**
```python
# Her grup için resolver çağrılır:
for ref_info in groups.get("credential", []):
    value = RefrenceResolver.get_credential_data(ref_info, session)
    resolved_params[ref_info["param_name"]] = value
```

**5. Nested Path Resolution:**
```python
# Örnek: "data.items[0].name"
path_parts = _resolve_nested_reference("data.items[0].name")
# Sonuç: ["data", "items", "[0]", "name"]

# Context'ten değer çıkarılır:
value = _get_value_from_context(path_parts, context)
# context = {"data": {"items": [{"name": "test"}]}}
# Sonuç: "test"
```

**6. Type Conversion:**
```python
# expected_type'a göre dönüşüm yapılır:
value = _convert_to_type(param_name, raw_value, expected_type)
# expected_type: "integer", "string", "float", "boolean", "array", "object"
```

---

## Önemli Notlar

### 1. Anlık Görüntü (Snapshot) Prensibi

- **ExecutionInput**: Node'un anlık görüntüsüdür
- Node silinse bile ExecutionInput kalır
- Script değiştirilse bile ExecutionInput'taki `script_path` değişmez
- Bu sayede execution'lar tutarlılığını korur

### 2. Referans Çözümleme

**Reference Format:**
- Format: `${type:id_or_value.path}`
- Örnekler:
  - `${static:30}` - Statik değer
  - `${trigger:data.user.id}` - Trigger data'dan
  - `${node:NOD-123.result.data}` - Önceki node'un output'undan
  - `${value:ENV-456}` - Variable'dan (workspace variable)
  - `${credential:CRD-789.api_key}` - Credential'dan
  - `${database:DBS-111.host}` - Database connection'dan
  - `${file:FLE-222.content}` - File'dan

**Reference Resolution Süreci:**
1. **Node Seviyesi**: Referanslar string olarak saklanır (`${credential:CRD-123.api_key}`)
2. **Parameter Resolution**: Referanslar parse edilir ve gruplandırılır (type, id, value_path)
3. **Reference Resolution**: Her grup için referanslar çözülür:
   - `value`: Variable'dan değer alınır (şifreli ise çözülür)
   - `credential`: Credential'dan değer alınır (şifreli ise çözülür, nested path desteklenir)
   - `node`: ExecutionOutput'tan değer alınır (nested path desteklenir)
   - `trigger`: Execution.trigger_data'dan değer alınır (nested path desteklenir)
   - `database`: Database connection string'den değer alınır
   - `file`: File content'ten değer alınır
   - `static`: Statik değer tip dönüşümü yapılır
4. **Context Seviyesi**: Referanslar çözülmüş değerler olarak saklanır (`"actual_secret_key_12345"`)
5. **Engine Seviyesi**: Sadece çözülmüş değerler kullanılır

### 3. Script Yolu Yönetimi

- **Script**: `file_path` disk yolu
- **Node**: Script'e referans (`script_id` veya `custom_script_id`)
- **ExecutionInput**: `script_path` kopyalanır (anlık görüntü)
- **Context**: `script_path` kopyalanır
- **Engine**: `script_path`'ten script yüklenir

### 4. Parametre Dönüşümü

- **Script → Node**: `input_schema` → `input_params` validasyonu
- **Node → ExecutionInput**: `input_params` → `params` (kopyalama)
- **ExecutionInput → Context**: `params` → `params` (referans çözümleme)
- **Context → Engine**: `params` → `params` (kopyalama)

---

## Özet

1. **Script**: Python kod dosyası, `input_schema` ve `output_schema` tanımlar
2. **Node**: Script'i workflow'a bağlar, `input_params` ile parametreleri tanımlar
3. **ExecutionInput**: Node'un anlık görüntüsü, execution için hazırlanır
4. **Context**: ExecutionInput'tan oluşturulur, referanslar çözülür
5. **Execution**: Context engine'e gönderilir, script çalıştırılır, sonuç toplanır

**Ana Dönüşümler:**
- Script'in `input_schema`'sı → Node'un `input_params` validasyonu
- Node'un `input_params`'ı → ExecutionInput'un `params`'ı (kopyalama)
- ExecutionInput'un `params`'ı → Context'in `params`'ı (referans çözümleme)
- Context'in `params`'ı → Engine'in `params`'ı (script'e gönderilir)

