# Workflow Yapısı ve Trigger İlişkisi

Bu dokümantasyon, MiniFlow Enterprise'da workflow yapısını, trigger ilişkilerini, node-script bağlantılarını ve durum yönetimini detaylı olarak açıklar.

## İçindekiler

1. [Workflow Genel Bakış](#workflow-genel-bakış)
2. [Workflow Oluşturma](#workflow-oluşturma)
3. [Workflow Durumları](#workflow-durumları)
4. [Trigger Yapısı](#trigger-yapısı)
5. [Workflow-Trigger İlişkisi](#workflow-trigger-ilişkisi)
6. [Node Yapısı](#node-yapısı)
7. [Node-Script İlişkisi](#node-script-ilişkisi)
8. [Edge Yapısı](#edge-yapısı)
9. [Durum Yönetimi](#durum-yönetimi)

---

## Workflow Genel Bakış

Workflow, bir iş akışını tanımlayan yapıdır. Bir workflow şunları içerir:

- **Nodes**: İş akışındaki adımlar (script'lerle bağlantılı)
- **Edges**: Node'lar arası bağlantılar (dependency graph)
- **Triggers**: Workflow'u tetikleyen mekanizmalar
- **Status**: Workflow'un durumu (DRAFT, ACTIVE, DEACTIVATED, ARCHIVED)

**Workflow Özellikleri:**
- Her workflow bir workspace'e aittir
- Workflow ismi workspace içinde benzersizdir
- Workflow'un bir priority değeri vardır (>= 1)
- Workflow oluşturulduğunda otomatik olarak DEFAULT trigger oluşturulur

---

## Workflow Oluşturma

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows`

**Request Body:**
```json
{
  "name": "string (required, unique within workspace)",
  "description": "string (optional)",
  "priority": "number (optional, default: 1, must be >= 1)",
  "tags": ["string"] (optional)
}
```

**Oluşturma Süreci:**

1. **Validasyon**: Name boş olamaz, priority >= 1 olmalı
2. **Workspace Kontrolü**: Workspace var mı kontrol edilir
3. **Limit Kontrolü**: Workspace'in workflow limiti kontrol edilir
4. **Benzersizlik Kontrolü**: Aynı isimde workflow var mı kontrol edilir
5. **Workflow Oluşturma**: Workflow DRAFT durumunda oluşturulur
6. **DEFAULT Trigger Oluşturma**: Otomatik olarak DEFAULT API trigger oluşturulur
   - Name: "DEFAULT"
   - Type: WEBHOOK
   - Config: {}
   - is_enabled: True
7. **Workspace Güncelleme**: Workspace'in `current_workflow_count` değeri artırılır

**Örnek Response:**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workflow created successfully. Default API trigger has been created.",
  "data": {
    "id": "WFL1234567890"
  }
}
```

---

## Workflow Durumları

### Durum Türleri

1. **DRAFT**: Workflow taslak durumunda
   - Oluşturulduğunda otomatik olarak DRAFT olur
   - Node'lar eklenebilir, düzenlenebilir
   - Aktif edilemez (en az bir node gerekir)

2. **ACTIVE**: Workflow aktif ve çalışmaya hazır
   - En az bir node olmalı
   - Tüm trigger'lar otomatik olarak enable edilir
   - Execution'lar başlatılabilir

3. **DEACTIVATED**: Workflow devre dışı
   - Tüm trigger'lar otomatik olarak disable edilir
   - Yeni execution'lar başlatılamaz
   - Mevcut execution'lar devam eder

4. **ARCHIVED**: Workflow arşivlenmiş
   - Değiştirilemez
   - Aktif edilemez
   - Sadece görüntülenebilir

### Durum Geçişleri

```
DRAFT → ACTIVE (activate_workflow)
ACTIVE → DEACTIVATED (deactivate_workflow)
DEACTIVATED → ACTIVE (activate_workflow)
ACTIVE/DEACTIVATED → ARCHIVED (archive_workflow)
ACTIVE/DEACTIVATED → DRAFT (set_draft) - ARCHIVED hariç
```

**Önemli Notlar:**
- ARCHIVED workflow'lar DRAFT'e dönemez
- ACTIVE olmak için en az bir node gerekir
- activate_workflow çağrıldığında tüm trigger'lar enable edilir
- deactivate_workflow çağrıldığında tüm trigger'lar disable edilir

---

## Trigger Yapısı

### Trigger Nedir?

Trigger, bir workflow'u tetikleyen mekanizmadır. Bir workflow'un birden fazla trigger'ı olabilir.

### Trigger Türleri

1. **API/WEBHOOK**: HTTP isteği ile tetiklenir
2. **SCHEDULED**: Cron expression ile zamanlanmış tetikleme
3. **EVENT**: Sistem event'leri ile tetiklenir

### Trigger Özellikleri

- **name**: Trigger adı (workspace içinde benzersiz)
- **trigger_type**: Trigger tipi (API, SCHEDULED, WEBHOOK, EVENT)
- **config**: Trigger konfigürasyonu (JSON)
  - SCHEDULED için: `{"cron_expression": "0 0 * * *"}`
- **input_mapping**: Input mapping kuralları (JSON)
- **is_enabled**: Trigger aktif mi? (boolean)
- **workflow_id**: Hangi workflow'u tetikler

### Trigger Limitleri

Her workflow için:
- **Minimum**: 1 trigger (varsayılan)
- **Maximum**: 10 trigger (varsayılan, config'den değiştirilebilir)

**Limit Kontrolü:**
- Trigger oluşturulurken limit kontrol edilir
- Limit aşılırsa hata döner: `Trigger limit reached for this workflow. Maximum: {max}`

### DEFAULT Trigger

Her workflow oluşturulduğunda otomatik olarak DEFAULT trigger oluşturulur:

- **Name**: "DEFAULT" (değiştirilemez)
- **Type**: WEBHOOK
- **Config**: {}
- **is_enabled**: True
- **Silinemez**: DEFAULT trigger silinemez

---

## Workflow-Trigger İlişkisi

### Otomatik Trigger Yönetimi

Workflow durumu değiştiğinde trigger'lar otomatik olarak yönetilir:

#### Workflow Activate Edildiğinde

```python
# WorkflowManagementService.activate_workflow()
1. Workflow status = ACTIVE yapılır
2. Workflow'un tüm trigger'ları getirilir
3. is_enabled=False olan trigger'lar enable edilir
```

**Sonuç**: Workflow aktif olduğunda tüm trigger'lar aktif hale gelir.

#### Workflow Deactivate Edildiğinde

```python
# WorkflowManagementService.deactivate_workflow()
1. Workflow status = DEACTIVATED yapılır
2. Workflow'un tüm trigger'ları getirilir
3. is_enabled=True olan trigger'lar disable edilir
```

**Sonuç**: Workflow deaktif olduğunda tüm trigger'lar deaktif hale gelir.

### Trigger Enable/Disable

Trigger'lar manuel olarak da enable/disable edilebilir:

**Enable Trigger:**
- **Endpoint**: `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/enable`
- **Sonuç**: `is_enabled = True`

**Disable Trigger:**
- **Endpoint**: `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/disable`
- **Sonuç**: `is_enabled = False`

**Önemli**: Workflow ACTIVE olsa bile, trigger manuel olarak disable edilirse execution başlatılamaz.

### Trigger Input Mapping

Trigger'lar input mapping kuralları tanımlayabilir:

**Format:**
```json
{
  "variable_name": {
    "type": "string|number|boolean|...",
    "value": "default_value",
    "required": true|false
  }
}
```

**Örnek:**
```json
{
  "api_key": {
    "type": "string",
    "value": "",
    "required": true
  },
  "timeout": {
    "type": "integer",
    "value": 30,
    "required": false
  }
}
```

Execution başlatılırken trigger_data bu mapping'e göre validate edilir.

---

## Node Yapısı

### Node Nedir?

Node, workflow içindeki bir adımdır. Her node bir script ile bağlantılıdır.

### Node Özellikleri

- **name**: Node adı (workflow içinde benzersiz)
- **script_id**: Global script ID (opsiyonel)
- **custom_script_id**: Custom script ID (opsiyonel)
- **input_params**: Node'un input parametreleri (script'in input_schema'sına göre)
- **output_params**: Node'un output parametreleri
- **meta_data**: Meta veriler (JSON)
- **max_retries**: Maksimum tekrar sayısı (varsayılan: 3)
- **timeout_seconds**: Timeout süresi (varsayılan: 300 saniye)

### Node Oluşturma

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/nodes`

**Request Body:**
```json
{
  "name": "string (required, unique within workflow)",
  "script_id": "string (optional, XOR with custom_script_id)",
  "custom_script_id": "string (optional, XOR with script_id)",
  "description": "string (optional)",
  "input_params": {} (optional, JSON - script'in input_schema'sına göre),
  "output_params": {} (optional, JSON),
  "meta_data": {} (optional, JSON),
  "max_retries": "number (optional, default: 3, must be >= 0)",
  "timeout_seconds": "number (optional, default: 300, must be > 0)"
}
```

**Önemli Kural**: Ya `script_id` ya da `custom_script_id` verilmeli (XOR). İkisi birden verilemez.

---

## Node-Script İlişkisi

### Script Seçimi

Node oluşturulurken iki tür script'ten biri seçilir:

1. **Global Script** (`script_id`): Tüm workspace'lerden erişilebilir
2. **Custom Script** (`custom_script_id`): Sadece aynı workspace'deki script'ler

**Kontrol:**
- Custom script seçildiğinde, script'in workspace_id'si workflow'un workspace_id'si ile aynı olmalı
- Script var mı kontrol edilir
- Script'in `file_path` değeri olmalı (script dosyası diskte olmalı)

### Input Params Validasyonu

Node oluşturulurken `input_params` script'in `input_schema`'sına göre validate edilir:

**Validasyon Adımları:**

1. **Schema Kontrolü**: `input_params` içindeki tüm parametreler `input_schema`'da tanımlı olmalı
2. **Required Kontrolü**: `required: true` olan parametreler mutlaka sağlanmalı
3. **Type Kontrolü**: Parametre değerleri şemada belirtilen tipe uygun olmalı
4. **Enum Kontrolü**: `enum` tanımlıysa, değer enum listesinde olmalı

**Input Params Formatı:**

Node'da saklanan format:
```json
{
  "param_name": {
    "type": "string",
    "value": "actual_value",
    "default_value": "default",
    "required": true,
    "description": "Parameter description"
  }
}
```

**Frontend Form Schema:**

Node'un form şeması alınırken script'in `input_schema`'sı frontend formatına dönüştürülür:

```json
{
  "param_name": {
    "front": {
      "order": 0,
      "type": "text|number|checkbox|select|...",
      "values": ["enum", "values"],
      "placeholder": "Enter param_name..."
    },
    "type": "string",
    "default_value": "default",
    "value": "current_value",
    "required": true,
    "description": "Parameter description"
  }
}
```

### Script Değişikliği

Node'un script'i değiştirildiğinde:

- Eğer yeni script'in `input_schema`'sı farklıysa, `input_params` reset edilebilir
- Node güncellenirken script değişikliği kontrol edilir

---

## Edge Yapısı

### Edge Nedir?

Edge, node'lar arası bağlantıdır. Dependency graph'ı oluşturur.

### Edge Özellikleri

- **from_node_id**: Kaynak node ID
- **to_node_id**: Hedef node ID
- **workflow_id**: Hangi workflow'a ait

### Edge Oluşturma

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/edges`

**Request Body:**
```json
{
  "from_node_id": "string (required)",
  "to_node_id": "string (required)"
}
```

**Kurallar:**
- Self-loop yasaktır (`from_node_id != to_node_id`)
- Her iki node da aynı workflow'a ait olmalı
- Edge oluşturulduğunda dependency graph güncellenir

### Dependency Graph

Edge'ler dependency graph oluşturur:

```
Node A → Node B → Node C
  ↓
Node D
```

Bu graph execution sırasında kullanılır:
- Node B, Node A tamamlanana kadar bekler
- Node C, Node B tamamlanana kadar bekler
- Node D, Node A tamamlanana kadar bekler

**Execution Input Oluşturulurken:**
- Her node için `dependency_count` hesaplanır
- `dependency_count`: O node'a gelen edge sayısı (kaç node'un tamamlanmasını bekliyor)

---

## Durum Yönetimi

### Workflow Durum Yönetimi

#### Activate Workflow

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/activate`

**Kurallar:**
- Workflow'da en az bir node olmalı
- Workflow zaten ACTIVE ise hata döner
- Workflow ACTIVE yapılır
- Tüm trigger'lar enable edilir

**Kod:**
```python
# WorkflowManagementService.activate_workflow()
1. Node sayısı kontrol edilir (>= 1)
2. Workflow status = ACTIVE
3. Tüm trigger'lar getirilir
4. is_enabled=False olanlar enable edilir
```

#### Deactivate Workflow

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/deactivate`

**Request Body:**
```json
{
  "reason": "string (optional)"
}
```

**Kurallar:**
- Workflow zaten DEACTIVATED ise hata döner
- Workflow DEACTIVATED yapılır
- Tüm trigger'lar disable edilir

**Kod:**
```python
# WorkflowManagementService.deactivate_workflow()
1. Workflow status = DEACTIVATED
2. Tüm trigger'lar getirilir
3. is_enabled=True olanlar disable edilir
```

#### Archive Workflow

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/archive`

**Kurallar:**
- Workflow ARCHIVED yapılır
- ARCHIVED workflow'lar değiştirilemez
- ARCHIVED workflow'lar aktif edilemez

#### Set Draft

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/set-draft`

**Kurallar:**
- ARCHIVED workflow'lar DRAFT'e dönemez
- Workflow DRAFT yapılır

### Trigger Durum Yönetimi

#### Enable Trigger

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/enable`

**Kurallar:**
- Trigger zaten enable ise hata döner
- `is_enabled = True` yapılır

#### Disable Trigger

**Endpoint:** `POST /frontend/workspaces/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/disable`

**Kurallar:**
- Trigger zaten disable ise hata döner
- `is_enabled = False` yapılır

**Önemli**: Workflow ACTIVE olsa bile, trigger disable edilirse execution başlatılamaz.

### Durum Matrisi

| Workflow Status | Trigger is_enabled | Execution Başlatılabilir mi? |
|----------------|-------------------|---------------------------|
| DRAFT | True/False | ❌ Hayır |
| ACTIVE | True | ✅ Evet |
| ACTIVE | False | ❌ Hayır (trigger disable) |
| DEACTIVATED | True/False | ❌ Hayır |
| ARCHIVED | True/False | ❌ Hayır |

---

## Özet

1. **Workflow Oluşturma**: DRAFT durumunda oluşturulur, DEFAULT trigger otomatik eklenir
2. **Durum Yönetimi**: ACTIVE/DEACTIVATED durumları trigger'ları otomatik yönetir
3. **Node-Script İlişkisi**: Node'lar script'lerle bağlantılı, input_params validate edilir
4. **Edge-Dependency**: Edge'ler dependency graph oluşturur, execution sırası belirlenir
5. **Trigger Yönetimi**: Trigger'lar manuel veya otomatik enable/disable edilebilir

