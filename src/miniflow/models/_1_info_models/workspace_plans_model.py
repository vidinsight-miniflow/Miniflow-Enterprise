"""
PLAN LIMITS MODEL - Plan Konfigürasyonları Tablosu
==================================================

Amaç:
    - Tüm plan tiplerinin (FREEMIUM, STARTER, PRO, BUSINESS, ENTERPRISE) limitlerini tanımlar
    - Workspace oluşturulurken bu değerler kopyalanır
    - Pricing (fiyatlandırma) bilgilerini içerir
    - Feature (özellik) matrisini JSON olarak tutar

İlişkiler:
    - YOK (Bağımsız yapılandırma tablosu)
    - Bu tablo seed data olarak doldurulur ve nadiren güncellenir

Workspace Limitleri (Per Workspace):
    - max_members_per_workspace: Her workspace'deki maksimum üye sayısı
    - max_workflows_per_workspace: Her workspace'deki maksimum workflow sayısı
    - max_custom_scripts_per_workspace: Her workspace'deki maksimum custom script sayısı (-1 = unlimited)
    
NOT: max_workspaces alanı YOK! Kullanıcı sınırsız ÜCRETLİ workspace oluşturabilir.
     Sadece ÜCRETSİZ workspace limiti var (kullanıcı başına maksimum 1 - iş mantığında kontrol)

Depolama Limitleri:
    - storage_limit_mb: Workspace başına depolama limiti (MB)
    - max_file_size_mb: Yüklenebilecek maksimum dosya boyutu (MB)

Execution (Çalıştırma) Limitleri:
    - monthly_execution_limit: Aylık çalıştırma limiti
    - max_concurrent_executions: Aynı anda çalışabilecek maksimum execution sayısı
    - max_execution_timeout_seconds: Bir execution'ın maksimum çalışma süresi (saniye)

İleri Özellikler (Boolean flags):
    - can_use_custom_scripts: Custom script yazabilir mi?
    - can_use_api_access: API erişimi var mı?
    - can_use_webhooks: Webhook kullanabilir mi?
    - can_use_scheduling: Zamanlama özelliği kullanabilir mi?
    - can_export_data: Veri export edebilir mi?
    - has_priority_support: Öncelikli destek var mı?
    - has_sla_guarantee: SLA garantisi var mı?

API Access Limitleri:
    - max_api_keys_per_workspace: Workspace başına maksimum API key sayısı (-1 = unlimited)
    - max_api_keys_per_workflow: Workflow başına maksimum API key sayısı (-1 = unlimited)
    - api_rate_limit_per_minute: API key için dakikalık istek limiti (patlama koruması)
    - api_rate_limit_per_hour: API key için saatlik istek limiti (-1 = unlimited)
    - api_rate_limit_per_day: API key için günlük istek limiti (-1 = unlimited)

Fiyatlandırma:
    - monthly_price_usd: Aylık ücret (USD)
    - yearly_price_usd: Yıllık ücret (USD) - genellikle indirimli
    - price_per_extra_member_usd: Ekstra üye başına ücret (USD)
    - price_per_extra_workflow_usd: Ekstra workflow başına ücret (USD)

Görünüm Bilgileri:
    - display_name: Plan görünen adı (örn: "Professional Plan")
    - description: Plan açıklaması
    - is_popular: Popüler plan işareti (UI'da öne çıkarmak için)
    - display_order: Sıralama için (0, 1, 2, ...)
    - features: Plan özelliklerinin JSON listesi

Veri Bütünlüğü:
    - UniqueConstraint: plan alanı benzersiz olmalı
    - Her plan için sadece 1 kayıt olmalı

Kullanım:
    1. Seed script ile tüm planlar için kayıt oluşturulur
    2. Workspace oluşturulurken user'ın planına göre limitler kopyalanır
    3. Plan upgrade/downgrade durumunda workspace limitleri güncellenir

Önemli Notlar:
    - Bu tablo SADECE OKUNUR (read-only) olarak kullanılmalıdır
    - Değişiklikler migration ile yapılmalıdır
    - ID prefix: WPL (örn: WPL-ABC123...)
"""

from sqlalchemy import Column, String, Integer, Boolean, Float, Text, JSON, UniqueConstraint, Enum

from ..base_model import BaseModel

class WorkspacePlans(BaseModel):
    """Plan limitleri ve özellik tanımları"""
    __prefix__ = "WPL"
    __tablename__ = 'workspace_plans'
    __table_args__ = (
        UniqueConstraint('name', name='_workspace_plan_name_unique'),
    )

    # Plan tanımlama
    name = Column(String(100), nullable=False, index=True)

    # Görünüm bilgileri
    display_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_popular = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Genel limitler
    max_members_per_workspace = Column(Integer, nullable=False)        # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    max_workflows_per_workspace = Column(Integer, nullable=False)      # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    max_custom_scripts_per_workspace = Column(Integer, nullable=True)  # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    storage_limit_mb_per_workspace = Column(Integer, nullable=False)   # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    max_file_size_mb_per_workspace = Column(Integer, nullable=False)   # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    
    # Aylık limitler
    monthly_execution_limit = Column(Integer, nullable=False)
    max_concurrent_executions = Column(Integer, nullable=False)        # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)

    # İleri özellikler
    can_use_custom_scripts = Column(Boolean, default=False, nullable=False)
    can_use_api_access = Column(Boolean, default=False, nullable=False)
    can_use_webhooks = Column(Boolean, default=False, nullable=False)
    can_use_scheduling = Column(Boolean, default=False, nullable=False)
    can_export_data = Column(Boolean, default=False, nullable=False)
    
    # API erişim limitleri
    max_api_keys_per_workspace = Column(Integer, nullable=True)     # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    api_rate_limit_per_minute = Column(Integer, nullable=True)      # Patlama koruması
    api_rate_limit_per_hour = Column(Integer, nullable=True)        # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    api_rate_limit_per_day = Column(Integer, nullable=True)         # -1 = sınırsız, null = sınırsız (geriye dönük uyumluluk)
    
    # Fiyatlandırma
    monthly_price_usd = Column(Float, nullable=False)
    yearly_price_usd = Column(Float, nullable=True)
    price_per_extra_member_usd = Column(Float, default=0.0, nullable=False)
    price_per_extra_workflow_usd = Column(Float, default=0.0, nullable=False)
    
    # Özellik açıklamaları
    features = Column(JSON, default=lambda: [], nullable=False)
    
    

