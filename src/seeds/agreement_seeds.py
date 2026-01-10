"""
Agreement Seeds
===============

Initial agreement versions for GDPR compliance.
Content is stored directly in database for legal proof.

Agreement Types:
    - terms: Kullanım Şartları
    - privacy_policy: Gizlilik Politikası
    - cookie_policy: Çerez Politikası
    - data_processing: Kişisel Verilerin İşlenmesi
"""

from datetime import datetime, timezone
import hashlib


def _generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash of content for integrity verification"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


# ============================================================================
# Kullanım Şartları (Terms of Service)
# ============================================================================

TERMS_TR_V1_0 = """# Kullanım Şartları

**Versiyon:** 1.0  
**Yürürlük Tarihi:** 1 Ocak 2025

## 1. Genel Hükümler

Bu kullanım şartları ("Şartlar"), Miniflow platformunun ("Platform") kullanımına ilişkin şartları ve koşulları belirler. Platform'u kullanarak bu Şartları kabul etmiş sayılırsınız.

## 2. Hizmet Tanımı

Miniflow, iş akışı otomasyonu ve entegrasyon platformudur. Platform üzerinden:
- Workflow oluşturabilir ve çalıştırabilirsiniz
- Farklı servisleri entegre edebilirsiniz
- Verilerinizi işleyebilir ve saklayabilirsiniz

## 3. Kullanıcı Yükümlülükleri

Kullanıcı olarak:
- Platform'u yasalara uygun kullanacağınızı
- Başkalarının haklarına saygı göstereceğinizi
- Sisteme zarar verecek aktivitelerden kaçınacağınızı
- Hesap bilgilerinizi gizli tutacağınızı taahhüt edersiniz.

## 4. Fikri Mülkiyet Hakları

Platform ve içeriği Miniflow'un fikri mülkiyetidir. Kullanıcılar:
- Platform'u lisans şartlarına uygun kullanabilir
- Kendi oluşturdukları workflow'ların sahibidir
- Platform üzerinde ürettikleri içeriği paylaşabilir

## 5. Sorumluluk Sınırlaması

Miniflow:
- Platform'u "olduğu gibi" sunar
- Kesintisiz hizmet garanti etmez
- Kullanıcı verilerinin yedeklenmesini tavsiye eder
- Dolaylı zararlardan sorumlu tutulamaz

## 6. Hesap Kapatma

Kullanıcılar hesaplarını istedikleri zaman kapatabilir. Miniflow, şartları ihlal eden hesapları askıya alabilir veya kapatabilir.

## 7. Değişiklikler

Bu Şartlar'da yapılacak değişiklikler kullanıcılara bildirilir. Değişikliklerden sonra Platform'u kullanmaya devam etmek, yeni şartları kabul ettiğiniz anlamına gelir.

## 8. İletişim

Sorularınız için: support@miniflow.com

---

**Son Güncelleme:** 1 Ocak 2025
"""

TERMS_EN_V1_0 = """# Terms of Service

**Version:** 1.0  
**Effective Date:** January 1, 2025

## 1. General Provisions

These Terms of Service ("Terms") govern your use of the Miniflow platform ("Platform"). By using the Platform, you agree to these Terms.

## 2. Service Description

Miniflow is a workflow automation and integration platform. Through the Platform you can:
- Create and execute workflows
- Integrate different services
- Process and store your data

## 3. User Obligations

As a user, you agree to:
- Use the Platform in compliance with applicable laws
- Respect the rights of others
- Refrain from activities that could harm the system
- Keep your account credentials confidential

## 4. Intellectual Property Rights

The Platform and its content are the intellectual property of Miniflow. Users:
- May use the Platform in accordance with license terms
- Own the workflows they create
- May share content they produce on the Platform

## 5. Limitation of Liability

Miniflow:
- Provides the Platform "as is"
- Does not guarantee uninterrupted service
- Recommends users back up their data
- Cannot be held liable for indirect damages

## 6. Account Termination

Users may close their accounts at any time. Miniflow may suspend or terminate accounts that violate these Terms.

## 7. Modifications

Changes to these Terms will be communicated to users. Continued use of the Platform after changes constitutes acceptance of the new terms.

## 8. Contact

For questions: support@miniflow.com

---

**Last Updated:** January 1, 2025
"""


# ============================================================================
# Gizlilik Politikası (Privacy Policy)
# ============================================================================

PRIVACY_POLICY_TR_V1_0 = """# Gizlilik Politikası

**Versiyon:** 1.0  
**Yürürlük Tarihi:** 1 Ocak 2025

## 1. Giriş

Bu Gizlilik Politikası, Miniflow platformunun kişisel verilerinizi nasıl topladığını, kullandığını ve koruduğunu açıklar.

## 2. Toplanan Veriler

Aşağıdaki kişisel verileri topluyoruz:

### 2.1 Hesap Bilgileri
- Ad, soyad
- E-posta adresi
- Kullanıcı adı
- Şifre (hashlenmiş)

### 2.2 Kullanım Verileri
- IP adresi (hashlenmiş)
- Tarayıcı bilgisi
- Platform kullanım istatistikleri
- Giriş geçmişi

### 2.3 Workflow Verileri
- Oluşturduğunuz workflow'lar
- Execution logları
- Entegrasyon ayarları

## 3. Verilerin Kullanım Amacı

Verilerinizi şu amaçlarla kullanıyoruz:
- Hizmet sunumu
- Güvenlik ve dolandırıcılık önleme
- Platform iyileştirme
- Yasal yükümlülüklerin yerine getirilmesi

## 4. Veri Güvenliği

Verilerinizi korumak için:
- SHA-256 şifreleme kullanıyoruz
- Düzenli güvenlik denetimleri yapıyoruz
- Erişim kontrolü uyguluyoruz
- Yedekleme sistemleri kullanıyoruz

## 5. GDPR Hakları

GDPR kapsamında sahip olduğunuz haklar:
- **Erişim Hakkı**: Verilerinize erişebilirsiniz
- **Düzeltme Hakkı**: Yanlış verileri düzeltebilirsiniz
- **Silme Hakkı**: Verilerinizin silinmesini talep edebilirsiniz
- **Taşınabilirlik Hakkı**: Verilerinizi indirebilirsiniz
- **İtiraz Hakkı**: Veri işlemeye itiraz edebilirsiniz

## 6. Çerezler

Platform, kullanıcı deneyimini iyileştirmek için çerezler kullanır. Çerez kullanımı hakkında detaylı bilgi için Çerez Politikamıza bakın.

## 7. Üçüncü Taraf Paylaşımı

Verilerinizi üçüncü taraflarla paylaşmıyoruz. Yalnızca yasal zorunluluk durumunda paylaşım yapılır.

## 8. Veri Saklama Süresi

- Aktif hesaplar: Hesap kapanana kadar
- Kapalı hesaplar: 30 gün sonra silme
- Log kayıtları: 90 gün
- Yasal gereklilik: İlgili mevzuat süresi

## 9. İletişim

Gizlilik ile ilgili sorularınız için: privacy@miniflow.com

---

**Son Güncelleme:** 1 Ocak 2025
"""

PRIVACY_POLICY_EN_V1_0 = """# Privacy Policy

**Version:** 1.0  
**Effective Date:** January 1, 2025

## 1. Introduction

This Privacy Policy explains how the Miniflow platform collects, uses, and protects your personal data.

## 2. Data Collection

We collect the following personal data:

### 2.1 Account Information
- First name, last name
- Email address
- Username
- Password (hashed)

### 2.2 Usage Data
- IP address (hashed)
- Browser information
- Platform usage statistics
- Login history

### 2.3 Workflow Data
- Workflows you create
- Execution logs
- Integration settings

## 3. Purpose of Data Use

We use your data for:
- Service provision
- Security and fraud prevention
- Platform improvement
- Legal compliance

## 4. Data Security

To protect your data, we:
- Use SHA-256 encryption
- Conduct regular security audits
- Implement access controls
- Use backup systems

## 5. GDPR Rights

Under GDPR, you have the right to:
- **Access**: Access your data
- **Rectification**: Correct inaccurate data
- **Erasure**: Request deletion of your data
- **Portability**: Download your data
- **Object**: Object to data processing

## 6. Cookies

The Platform uses cookies to improve user experience. See our Cookie Policy for details.

## 7. Third-Party Sharing

We do not share your data with third parties, except when legally required.

## 8. Data Retention

- Active accounts: Until account closure
- Closed accounts: Deleted after 30 days
- Log records: 90 days
- Legal requirements: As required by law

## 9. Contact

For privacy questions: privacy@miniflow.com

---

**Last Updated:** January 1, 2025
"""


# ============================================================================
# Seed Data
# ============================================================================

AGREEMENT_SEEDS = [
    # Kullanım Şartları - Türkçe
    {
        "agreement_type": "terms",
        "version": "1.0",
        "content": TERMS_TR_V1_0,
        "content_hash": _generate_content_hash(TERMS_TR_V1_0),
        "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "is_active": True,
        "locale": "tr-TR",
        "created_by": None,  # System
        "notes": "İlk versiyon - Platform lansmanı"
    },
    
    # Kullanım Şartları - İngilizce
    {
        "agreement_type": "terms",
        "version": "1.0",
        "content": TERMS_EN_V1_0,
        "content_hash": _generate_content_hash(TERMS_EN_V1_0),
        "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "is_active": True,
        "locale": "en-US",
        "created_by": None,  # System
        "notes": "Initial version - Platform launch"
    },
    
    # Gizlilik Politikası - Türkçe
    {
        "agreement_type": "privacy_policy",
        "version": "1.0",
        "content": PRIVACY_POLICY_TR_V1_0,
        "content_hash": _generate_content_hash(PRIVACY_POLICY_TR_V1_0),
        "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "is_active": True,
        "locale": "tr-TR",
        "created_by": None,  # System
        "notes": "İlk versiyon - GDPR uyumlu"
    },
    
    # Gizlilik Politikası - İngilizce
    {
        "agreement_type": "privacy_policy",
        "version": "1.0",
        "content": PRIVACY_POLICY_EN_V1_0,
        "content_hash": _generate_content_hash(PRIVACY_POLICY_EN_V1_0),
        "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "is_active": True,
        "locale": "en-US",
        "created_by": None,  # System
        "notes": "Initial version - GDPR compliant"
    },
]

