from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import hashlib

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class AgreementService:
    """
    Sözleşme versiyonları servis katmanı.
    
    AgreementVersion tablosu terms, privacy_policy gibi sözleşmelerin
    versiyonlarını yönetir. Her tip için sadece bir aktif versiyon olabilir.
    """
    _registry = RepositoryRegistry()
    _agreement_repo = _registry.agreement_version_repository()

    # ==================================================================================== SEED ==
    @classmethod
    @with_transaction(manager=None)
    def seed_default_agreements(
        cls,
        session,
        *,
        agreements_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Varsayılan sözleşmeleri seed eder.
        
        Args:
            agreements_data: Sözleşme verilerinin listesi
            
        Returns:
            {"created": int, "skipped": int, "invalid": int}
        """
        stats = {"created": 0, "skipped": 0, "invalid": 0}

        for agreement_data in agreements_data:
            agreement_type = agreement_data.get("agreement_type")
            version = agreement_data.get("version")
            locale = agreement_data.get("locale", "tr-TR")

            if not agreement_type or not version:
                stats["invalid"] += 1
                continue

            existing = cls._agreement_repo._get_by_type_and_version(
                session,
                agreement_type=agreement_type,
                version=version,
                locale=locale
            )

            if existing:
                stats["skipped"] += 1
            else:
                # content_hash hesapla
                content = agreement_data.get("content", "")
                if "content_hash" not in agreement_data:
                    agreement_data["content_hash"] = hashlib.sha256(content.encode()).hexdigest()
                
                cls._agreement_repo._create(session, **agreement_data)
                stats["created"] += 1

        return stats

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_all_agreements(
        cls,
        session
    ) -> List[Dict[str, Any]]:
        """
        Tüm sözleşme versiyonlarını getirir.
        
        Returns:
            Sözleşme listesi
        """
        agreements = cls._agreement_repo._get_all(session, include_deleted=False)
        return [agreement.to_dict() for agreement in agreements]

    @classmethod
    @with_readonly_session(manager=None)
    def get_active_agreements(
        cls,
        session,
        *,
        locale: str = "tr-TR"
    ) -> List[Dict[str, Any]]:
        """
        Tüm aktif sözleşmeleri getirir (her tip için bir tane).
        
        Args:
            locale: Dil kodu
            
        Returns:
            Aktif sözleşme listesi
        """
        agreements = cls._agreement_repo._get_all(session, include_deleted=False)
        active_list = [
            agreement.to_dict() 
            for agreement in agreements 
            if agreement.is_active and agreement.locale == locale
        ]
        return active_list

    @classmethod
    @with_readonly_session(manager=None)
    def get_agreement_by_id(
        cls,
        session,
        *,
        agreement_id: str
    ) -> Dict[str, Any]:
        """
        ID ile sözleşme versiyonunu getirir.
        
        Args:
            agreement_id: Sözleşme ID'si
            
        Returns:
            Sözleşme detayları
            
        Raises:
            ResourceNotFoundError: Sözleşme bulunamazsa
        """
        agreement = cls._agreement_repo._get_by_id(session, record_id=agreement_id, raise_not_found=True)
        return agreement.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_active_agreement_by_type(
        cls,
        session,
        *,
        agreement_type: str,
        locale: str = "tr-TR"
    ) -> Dict[str, Any]:
        """
        Belirtilen tip için aktif sözleşmeyi getirir.
        
        Args:
            agreement_type: Sözleşme tipi (terms, privacy_policy, vb)
            locale: Dil kodu
            
        Returns:
            Aktif sözleşme detayları
            
        Raises:
            ResourceNotFoundError: Aktif sözleşme bulunamazsa
        """
        agreement = cls._agreement_repo._get_active(
            session,
            agreement_type=agreement_type,
            locale=locale,
            include_deleted=False
        )
        if not agreement:
            raise ResourceNotFoundError(
                resource_name="agreement_version",
                message=f"No active agreement found for type '{agreement_type}' and locale '{locale}'"
            )
        return agreement.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_agreement_by_type_and_version(
        cls,
        session,
        *,
        agreement_type: str,
        version: str,
        locale: str = "tr-TR"
    ) -> Dict[str, Any]:
        """
        Tip, versiyon ve locale ile sözleşmeyi getirir.
        
        Args:
            agreement_type: Sözleşme tipi
            version: Versiyon numarası
            locale: Dil kodu
            
        Returns:
            Sözleşme detayları
            
        Raises:
            ResourceNotFoundError: Sözleşme bulunamazsa
        """
        agreement = cls._agreement_repo._get_by_type_and_version(
            session,
            agreement_type=agreement_type,
            version=version,
            locale=locale,
            include_deleted=False
        )
        if not agreement:
            raise ResourceNotFoundError(
                resource_name="agreement_version",
                message=f"Agreement not found: {agreement_type} v{version} ({locale})"
            )
        return agreement.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_all_versions_by_type(
        cls,
        session,
        *,
        agreement_type: str,
        locale: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Belirtilen tip için tüm versiyonları getirir.
        
        Args:
            agreement_type: Sözleşme tipi
            locale: Dil kodu (opsiyonel)
            
        Returns:
            Versiyon listesi (effective_date'e göre sıralı)
        """
        agreements = cls._agreement_repo._get_all_by_type(
            session,
            agreement_type=agreement_type,
            locale=locale,
            include_deleted=False
        )
        return [agreement.to_dict() for agreement in agreements]

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_agreement_version(
        cls,
        session,
        *,
        agreement_type: str,
        version: str,
        content: str,
        effective_date: datetime,
        locale: str = "tr-TR",
        is_active: bool = False,
        created_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Yeni sözleşme versiyonu oluşturur.
        
        Args:
            agreement_type: Sözleşme tipi
            version: Versiyon numarası
            content: Sözleşme içeriği (Markdown)
            effective_date: Yürürlük tarihi
            locale: Dil kodu
            is_active: Aktif mi?
            created_by: Oluşturan kullanıcı ID'si
            notes: Versiyon notları
            
        Returns:
            Oluşturulan sözleşme
            
        Raises:
            ResourceAlreadyExistsError: Aynı tip/versiyon/locale varsa
        """
        # Aynı kombinasyon var mı kontrol et
        existing = cls._agreement_repo._get_by_type_and_version(
            session,
            agreement_type=agreement_type,
            version=version,
            locale=locale
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="agreement_version",
                message=f"Agreement already exists: {agreement_type} v{version} ({locale})"
            )

        # Content hash hesapla
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Eğer aktif olarak işaretlendiyse, aynı tip/locale için diğerlerini pasif yap
        if is_active:
            cls._deactivate_others(session, agreement_type=agreement_type, locale=locale)

        agreement = cls._agreement_repo._create(
            session,
            agreement_type=agreement_type,
            version=version,
            content=content,
            content_hash=content_hash,
            effective_date=effective_date,
            locale=locale,
            is_active=is_active,
            created_by=created_by,
            notes=notes
        )
        return agreement.to_dict()

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def activate_agreement(
        cls,
        session,
        *,
        agreement_id: str
    ) -> Dict[str, Any]:
        """
        Belirtilen sözleşmeyi aktif yapar.
        Aynı tip/locale için diğer versiyonlar pasif yapılır.
        
        Args:
            agreement_id: Sözleşme ID'si
            
        Returns:
            Güncellenmiş sözleşme
            
        Raises:
            ResourceNotFoundError: Sözleşme bulunamazsa
        """
        agreement = cls._agreement_repo._get_by_id(session, record_id=agreement_id, raise_not_found=True)
        
        # Aynı tip/locale için diğerlerini pasif yap
        cls._deactivate_others(
            session, 
            agreement_type=agreement.agreement_type, 
            locale=agreement.locale,
            exclude_id=agreement_id
        )
        
        # Bu versiyonu aktif yap
        updated = cls._agreement_repo._update(session, record_id=agreement_id, is_active=True)
        return updated.to_dict()

    @classmethod
    @with_transaction(manager=None)
    def deactivate_agreement(
        cls,
        session,
        *,
        agreement_id: str
    ) -> Dict[str, Any]:
        """
        Belirtilen sözleşmeyi pasif yapar.
        
        Args:
            agreement_id: Sözleşme ID'si
            
        Returns:
            Güncellenmiş sözleşme
            
        Raises:
            ResourceNotFoundError: Sözleşme bulunamazsa
        """
        cls._agreement_repo._get_by_id(session, record_id=agreement_id, raise_not_found=True)
        updated = cls._agreement_repo._update(session, record_id=agreement_id, is_active=False)
        return updated.to_dict()

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_agreement(
        cls,
        session,
        *,
        agreement_id: str
    ) -> bool:
        """
        Belirtilen sözleşmeyi soft-delete yapar.
        
        Args:
            agreement_id: Sözleşme ID'si
            
        Returns:
            True
            
        Raises:
            ResourceNotFoundError: Sözleşme bulunamazsa
        """
        cls._agreement_repo._get_by_id(session, record_id=agreement_id, raise_not_found=True)
        cls._agreement_repo._soft_delete(session, record_id=agreement_id)
        return True

    # ==================================================================================== HELPER ==
    @classmethod
    def _deactivate_others(
        cls,
        session,
        *,
        agreement_type: str,
        locale: str,
        exclude_id: Optional[str] = None
    ) -> None:
        """Aynı tip/locale için diğer versiyonları pasif yapar."""
        agreements = cls._agreement_repo._get_all_by_type(
            session,
            agreement_type=agreement_type,
            locale=locale,
            include_deleted=False
        )
        for agreement in agreements:
            if agreement.is_active and (exclude_id is None or agreement.id != exclude_id):
                cls._agreement_repo._update(session, record_id=agreement.id, is_active=False)
