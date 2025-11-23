"""
NOTIFICATION MODEL - Kullanıcı Bildirimleri Tablosu
===================================================

Amaç:
    - Tüm bildirim tiplerini yönetir (email, SMS, push, in-app, webhook)
    - Bildirim teslimat durumunu takip eder
    - Bildirim şablonlarını destekler
    - Öncelik bazlı bildirim kuyruğu
    - Kategorize edilmiş bildirimler ve süre dolma desteği

İlişkiler:
    - User (user) - Bildirimi alan kullanıcı [N:1]
    - User (sent_by) - Bildirimi tetikleyen kullanıcı [N:1, nullable]

Temel Alanlar:
    - user_id: Alıcı kullanıcı ID'si
    - type: Bildirim kanalı (EMAIL, SMS, PUSH, IN_APP, WEBHOOK)
    - status: Teslimat durumu (PENDING, SENT, DELIVERED, FAILED, READ)
    - priority: Öncelik seviyesi (LOW, NORMAL, HIGH, URGENT)
    - is_system: Sistem tarafından oluşturulan vs kullanıcı tarafından oluşturulan bildirim
    - is_read: Hızlı okunmamış sorgular için boolean flag (indeksli)
    - category: Bildirim kategorisi (SYSTEM, USER, SECURITY, WORKFLOW, vb.)
    - is_dismissible: Kullanıcı bu bildirimi kapatabilir mi?
    - expires_at: Bu zamandan sonra otomatik silme (geçici bildirimler için)
    - title: Bildirim başlığı/konusu
    - message: Bildirim içeriği/gövdesi
    - action_url: Opsiyonel aksiyon linki
    - template_id: Opsiyonel şablon referansı
    - template_data: Şablon değişkenleri (JSON)

Teslimat Takibi:
    - sent_at: Bildirim ne zaman gönderildi
    - delivered_at: Bildirim ne zaman teslim edildi
    - read_at: Bildirim ne zaman okundu (sadece in-app)
    - failed_at: Teslimat ne zaman başarısız oldu
    - failure_reason: Başarısızlık nedeni

Üst Veri:
    - notification_metadata: Ek veri (JSON)
    - retry_count: Retry deneme sayısı
    - max_retries: Maksimum retry deneme sayısı

Performans:
    - is_read hızlı okunmamış sorgular için indekslenmiş (WHERE is_read = False)
    - category filtreleme için indekslenmiş (WHERE category = 'SECURITY')
    - expires_at temizleme işleri için indekslenmiş

Önemli Notlar:
    - Kullanıcı silindiğinde bildirimler de silinir (CASCADE)
    - Çoklu bildirim kanallarını destekler
    - Sistem bildirimleri: is_system=True, sent_by=NULL
    - Geçici bildirimler: expires_at otomatik temizleme için ayarlanır
    - ID prefix: NOT (örn: NOT-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum, Index, Boolean
from datetime import datetime, timezone

from ..base_model import BaseModel
from ..enums import NotificationType, NotificationStatus, NotificationPriority, NotificationCategory


class Notification(BaseModel):
    """Çoklu kanal desteği ile kullanıcı bildirimleri"""
    __prefix__ = "NOT"
    __tablename__ = 'notifications'
    __table_args__ = (
        # Yaygın sorgular için indeksler
        Index('idx_notification_user_status', 'user_id', 'status'),
        Index('idx_notification_user_type', 'user_id', 'type'),
        Index('idx_notification_user_read', 'user_id', 'is_read'),  # Hızlı okunmamış sorgu
        Index('idx_notification_user_category', 'user_id', 'category'),  # Kategoriye göre filtreleme
        Index('idx_notification_status_priority', 'status', 'priority'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_expires', 'expires_at'),  # Süresi dolmuş temizleme
    )

    # ========================================================================
    # ALICI VE GÖNDEREN
    # ========================================================================
    user_id = Column(
        String(20),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Bildirim alıcısı"
    )
    
    sent_by = Column(
        String(20),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="Bildirimi tetikleyen kullanıcı (opsiyonel)"
    )

    # ========================================================================
    # BİLDİRİM TİPİ VE DURUMU
    # ========================================================================
    type = Column(
        Enum(NotificationType),
        nullable=False,
        index=True,
        comment="Bildirim kanalı (EMAIL, SMS, PUSH, IN_APP, WEBHOOK)"
    )
    
    status = Column(
        Enum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
        comment="Teslimat durumu"
    )
    
    priority = Column(
        Enum(NotificationPriority),
        default=NotificationPriority.NORMAL,
        nullable=False,
        index=True,
        comment="Öncelik seviyesi"
    )

    # ========================================================================
    # BİLDİRİM KATEGORİZASYONU VE BAYRAKLAR
    # ========================================================================
    is_system = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Sistem tarafından oluşturulan bildirim (kullanıcı tarafından oluşturulana karşı)"
    )
    
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Okunma durumu (read_at kontrolünden daha hızlı)"
    )
    
    category = Column(
        Enum(NotificationCategory),
        default=NotificationCategory.SYSTEM,
        nullable=False,
        index=True,
        comment="Filtreleme için bildirim kategorisi"
    )
    
    is_dismissible = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Kullanıcı bu bildirimi kapatabilir mi?"
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Bu zamandan sonra otomatik silme (geçici bildirimler için)"
    )

    # ========================================================================
    # BİLDİRİM İÇERİĞİ
    # ========================================================================
    title = Column(
        String(255),
        nullable=False,
        comment="Bildirim başlığı/konusu"
    )
    
    message = Column(
        Text,
        nullable=False,
        comment="Bildirim içeriği/gövdesi"
    )
    
    action_url = Column(
        Text,
        nullable=True,
        comment="Opsiyonel aksiyon linki (in-app/email bildirimleri için)"
    )
    
    action_text = Column(
        String(100),
        nullable=True,
        comment="Aksiyon butonu metni (örn: 'Workflow Görüntüle', 'Daveti Kabul Et')"
    )

    # ========================================================================
    # ŞABLON DESTEĞİ
    # ========================================================================
    template_id = Column(
        String(100),
        nullable=True,
        comment="Opsiyonel şablon tanımlayıcısı"
    )
    
    template_data = Column(
        JSON,
        default=lambda: {},
        nullable=False,
        comment="Şablon değişkenleri (JSON)"
    )

    # ========================================================================
    # TESLİMAT TAKİBİ
    # ========================================================================
    sent_at = Column(
        DateTime,
        nullable=True,
        comment="Bildirim ne zaman gönderildi"
    )
    
    delivered_at = Column(
        DateTime,
        nullable=True,
        comment="Bildirim ne zaman teslim edildi (email/sms)"
    )
    
    read_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Bildirim ne zaman okundu (sadece in-app)"
    )
    
    failed_at = Column(
        DateTime,
        nullable=True,
        comment="Teslimat ne zaman başarısız oldu"
    )
    
    failure_reason = Column(
        Text,
        nullable=True,
        comment="Teslimat başarısızlık nedeni"
    )

    # ========================================================================
    # RETRY MEKANİZMASI
    # ========================================================================
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Retry deneme sayısı"
    )
    
    max_retries = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Maksimum retry deneme sayısı"
    )

    # ========================================================================
    # KANAL ÖZEL VERİLER
    # ========================================================================
    recipient_email = Column(
        String(255),
        nullable=True,
        comment="E-posta adresi (EMAIL tipi için)"
    )
    
    recipient_phone = Column(
        String(20),
        nullable=True,
        comment="Telefon numarası (SMS tipi için)"
    )
    
    webhook_url = Column(
        Text,
        nullable=True,
        comment="Webhook URL (WEBHOOK tipi için)"
    )
    
    push_token = Column(
        Text,
        nullable=True,
        comment="Push bildirim token'ı (PUSH tipi için)"
    )

    # ========================================================================
    # ÜST VERİ
    # ========================================================================
    notification_metadata = Column(
        JSON,
        default=lambda: {},
        nullable=False,
        comment="Ek bildirim verisi"
    )
    
    provider_response = Column(
        JSON,
        nullable=True,
        comment="Harici sağlayıcıdan gelen yanıt (SendGrid, Twilio, vb.)"
    )

    # ========================================================================
    # İLİŞKİLER
    # ========================================================================
    user = relationship(
        "User",
        foreign_keys="[Notification.user_id]",
        back_populates="notifications"
    )
    
    sender = relationship(
        "User",
        foreign_keys="[Notification.sent_by]"
    )

    # ========================================================================
    # YARDIMCI METODLAR
    # ========================================================================
    @property
    def is_sent(self):
        """Bildirimin gönderilip gönderilmediğini kontrol et"""
        return self.status in [
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.READ
        ]
    
    @property
    def is_failed(self):
        """Bildirim teslimatının başarısız olup olmadığını kontrol et"""
        return self.status in [NotificationStatus.FAILED, NotificationStatus.BOUNCED]
    
    @property
    def can_retry(self):
        """Bildirimin tekrar denenip denenemeyeceğini kontrol et"""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def is_expired(self):
        """Bildirimin süresinin dolup dolmadığını kontrol et"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def mark_as_read(self):
        """Bildirimi okundu olarak işaretle (hem is_read bayrağını hem de read_at zaman damgasını günceller)"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)
            self.status = NotificationStatus.READ

