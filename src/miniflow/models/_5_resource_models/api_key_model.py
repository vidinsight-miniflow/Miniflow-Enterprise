"""
API KEY MODEL - API Anahtarları Tablosu
=======================================

Amaç:
    - Workspace içinde kullanılan API key'leri yönetir
    - User ve Workspace bazlı programatik erişim
    - Rate limiting ve izin takibi

İlişkiler:
    - User (user) - API key sahibi [N:1] 
    - Workspace (workspace) - Hangi workspace'de [N:1]

Önemli Kısıtlama:
    - Her API key BİR user'a aittir
    - Her API key BİR workspace'de kullanılabilir
    - Aynı user + workspace kombinasyonu için birden fazla key olabilir (name ile ayrılır)

Temel Alanlar:
    - workspace_id: Hangi workspace'de
    - user_id: API key sahibi (kim oluşturdu)
    - name: API key adı (user+workspace bazında benzersiz)
    - key_prefix: Görünen prefix (sk_live_, sk_test_)
    - key_hash: Tam key hash (güvenli saklama)
    - permissions: API key izinleri (JSON)

Durum:
    - is_active: API key aktif mi?
    - expires_at: Geçerlilik süresi bitiş tarihi
    - last_used_at: Son kullanım zamanı
    - usage_count: Kullanım sayısı

İstek Limiti:
    - rate_limit_per_minute: Dakikada maksimum istek sayısı
    - rate_limit_per_hour: Saatte maksimum istek sayısı
    - rate_limit_per_day: Günde maksimum istek sayısı

Üst Veri:
    - description: API key açıklaması
    - tags: Etiketler (JSON array)
    - allowed_ips: İzin verilen IP adresleri (JSON array)

Veri Bütünlüğü:
    - UniqueConstraint: (workspace_id, name) benzersiz olmalı
    - Unique: key_hash benzersiz olmalı (global)

Güvenlik En İyi Uygulamaları:
    - key_hash bcrypt veya argon2 ile hashlenmiş saklanmalı
    - Tam key sadece oluşturma anında gösterilir, sonra erişilemez
    - key_prefix görüntülemek için kullanılır (sk_live_****...)
    - Son kullanma tarihi ayarlanmalı (maksimum 1 yıl önerilir)

Önemli Notlar:
    - Workspace silindiğinde API key'ler de silinir (CASCADE)
    - API key ile yapılan işlemler triggered_by'da "api_key:{key_id}" olarak loglanır
    - BaseModel'den created_by kullanılır (kim oluşturdu)
    - ID prefix: API (örn: API-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint

from ..base_model import BaseModel


class ApiKey(BaseModel):
    """API anahtarları"""
    __prefix__ = "API"
    __tablename__ = 'api_keys'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_api_key_name_unique'),
        # Kaldırıldı: workflow_id ile UniqueConstraint (workflow_id kolonu kaldırıldı)
    )

    # İlişkiler - User ve Workspace
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Temel bilgiler
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Key bilgileri - Güvenlik
    key_prefix = Column(String(20), nullable=False)  # örn: "sk_live_", "sk_test_"
    key_hash = Column(String(255), nullable=False, unique=True)  # Tam key hashlenmiş
    
    # İzinler - Detaylı izinler ile JSON
    permissions = Column(JSON, default=lambda: {
        "workflows": {
            "execute": True,
            "read": True,
            "write": False,
            "delete": False
        },
        "credentials": {
            "read": True,
            "write": False,
            "delete": False
        },
        "databases": {
            "read": True,
            "write": False,
            "delete": False
        },
        "variables": {
            "read": True,
            "write": False,
            "delete": False
        },
        "files": {
            "read": True,
            "write": False,
            "delete": False
        }
    }, 
    nullable=False,
    comment="API key izinleri"
    )
    
    # Durum
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Güvenlik - IP beyaz listesi
    allowed_ips = Column(JSON, default=lambda: [], nullable=True)  # [] = tüm IP'lere izin verilir
    
    # Üst veri
    tags = Column(JSON, default=lambda: [], nullable=True)

    # İlişkiler
    workspace = relationship("Workspace", back_populates="api_keys")
    owner = relationship("User", foreign_keys="[ApiKey.owner_id]", back_populates="api_keys")