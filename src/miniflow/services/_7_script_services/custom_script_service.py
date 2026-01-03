from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import ScriptApprovalStatus, ScriptTestStatus
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.file_helper import (
    upload_custom_script,
    delete_file,
)

# Logger instance
logger = get_logger(__name__)

class CustomScriptService:
    """
    Custom (Workspace) script yönetim servisi.
    
    Workspace'e özel script'lerin yüklenmesi, onay workflow'u ve yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    NOT: Script içeriği oluşturulduktan sonra DEĞİŞTİRİLEMEZ (güvenlik).
    """
    _registry = RepositoryRegistry()
    _custom_script_repo = _registry.custom_script_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_custom_script(
        cls,
        session,
        *,
        workspace_id: str,
        uploaded_by: str,
        name: str,
        content: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        required_packages: Optional[List[str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Custom script oluşturur.
        
        - Workspace script limiti kontrol edilir
        - Script dosyası diske yazılır
        - Varsayılan olarak PENDING approval status ile oluşturulur
        
        Args:
            workspace_id: Workspace ID'si
            uploaded_by: Yükleyen kullanıcı ID'si
            name: Script adı (workspace içinde benzersiz)
            content: Script içeriği
            description: Açıklama (opsiyonel)
            category: Kategori (opsiyonel)
            subcategory: Alt kategori (opsiyonel)
            required_packages: Gerekli paketler (opsiyonel)
            input_schema: Input şeması (opsiyonel)
            output_schema: Output şeması (opsiyonel)
            tags: Etiketler (opsiyonel)
            documentation_url: Dökümantasyon URL'i (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Script name cannot be empty"
            )
        
        if not content or not content.strip():
            raise InvalidInputError(
                field_name="content",
                message="Script content cannot be empty"
            )
        
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Limit kontrolü
        if workspace.current_custom_script_count >= workspace.custom_script_limit:
            raise BusinessRuleViolationError(
                rule_name="script_limit_reached",
                rule_detail=f"Workspace {workspace_id} has {workspace.current_custom_script_count} custom scripts, limit is {workspace.custom_script_limit}",
                message=f"Custom script limit reached. Maximum: {workspace.custom_script_limit}"
            )
        
        # Benzersizlik kontrolü
        existing = cls._custom_script_repo._get_by_name(
            session, 
            workspace_id=workspace_id, 
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="CustomScript",
                conflicting_field="name",
                message=f"Custom script with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # Script dosyasını yükle
        file_extension = ".py"
        try:
            upload_result = upload_custom_script(
                content=content,
                script_name=name,
                extension=file_extension,
                workspace_id=workspace_id,
                category=category,
                subcategory=subcategory
            )
            file_path = upload_result["file_path"]
            file_size = upload_result["file_size"]
        except Exception as e:
            raise InvalidInputError(
                field_name="content",
                message=f"Failed to upload script: {str(e)}"
            )
        
        # Script oluştur
        script = cls._custom_script_repo._create(
            session,
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            name=name,
            content=content,
            description=description,
            file_extension=file_extension,
            file_size=file_size,
            file_path=file_path,
            category=category,
            subcategory=subcategory,
            required_packages=required_packages or [],
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            tags=tags or [],
            documentation_url=documentation_url,
            approval_status=ScriptApprovalStatus.PENDING,
            test_status=ScriptTestStatus.UNTESTED,
            is_dangerous=False,
            created_by=uploaded_by
        )
        
        # Workspace script sayısını güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            current_custom_script_count=workspace.current_custom_script_count + 1
        )
        
        return {"id": script.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_custom_script(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Custom script detaylarını getirir (content hariç).
        
        Args:
            script_id: Script ID'si
            
        Returns:
            Script detayları
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        return {
            "id": script.id,
            "workspace_id": script.workspace_id,
            "uploaded_by": script.uploaded_by,
            "name": script.name,
            "description": script.description,
            "file_extension": script.file_extension,
            "file_size": script.file_size,
            "category": script.category,
            "subcategory": script.subcategory,
            "required_packages": script.required_packages,
            "input_schema": script.input_schema,
            "output_schema": script.output_schema,
            "tags": script.tags,
            "documentation_url": script.documentation_url,
            "approval_status": script.approval_status.value if script.approval_status else None,
            "reviewed_by": script.reviewed_by,
            "reviewed_at": script.reviewed_at.isoformat() if script.reviewed_at else None,
            "review_notes": script.review_notes,
            "test_status": script.test_status.value if script.test_status else None,
            "test_coverage": script.test_coverage,
            "is_dangerous": script.is_dangerous,
            "created_at": script.created_at.isoformat() if script.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_script_content(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script içeriğini ve şemalarını getirir.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"content": str, "input_schema": Dict, "output_schema": Dict}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        return {
            "content": script.content,
            "input_schema": script.input_schema,
            "output_schema": script.output_schema
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_scripts(
        cls,
        session,
        *,
        workspace_id: str,
        category: Optional[str] = None,
        approval_status: Optional[ScriptApprovalStatus] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in script'lerini listeler.
        
        Args:
            workspace_id: Workspace ID'si
            category: Kategori filtresi (opsiyonel)
            approval_status: Onay durumu filtresi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "scripts": List[Dict], "count": int}
        """
        if approval_status:
            scripts = cls._custom_script_repo._get_by_approval_status(
                session, 
                workspace_id=workspace_id, 
                approval_status=approval_status
            )
        elif category:
            scripts = cls._custom_script_repo._get_by_category(
                session, 
                workspace_id=workspace_id, 
                category=category
            )
        else:
            scripts = cls._custom_script_repo._get_all_by_workspace_id(
                session, 
                workspace_id=workspace_id
            )
        
        return {
            "workspace_id": workspace_id,
            "scripts": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "category": s.category,
                    "subcategory": s.subcategory,
                    "file_size": s.file_size,
                    "approval_status": s.approval_status.value if s.approval_status else None,
                    "test_status": s.test_status.value if s.test_status else None,
                    "is_dangerous": s.is_dangerous,
                    "tags": s.tags,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in scripts
            ],
            "count": len(scripts)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_custom_script(
        cls,
        session,
        *,
        script_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Script meta bilgilerini günceller.
        
        NOT: Script içeriği DEĞİŞTİRİLEMEZ! Güvenlik nedeniyle yeni script oluşturun.
        
        Args:
            script_id: Script ID'si
            description: Yeni açıklama (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            documentation_url: Yeni dökümantasyon URL'i (opsiyonel)
            
        Returns:
            Güncellenmiş script bilgileri
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        if documentation_url is not None:
            update_data["documentation_url"] = documentation_url
        
        if update_data:
            cls._custom_script_repo._update(session, record_id=script_id, **update_data)
        
        return cls.get_custom_script(script_id=script_id)

    # ==================================================================================== APPROVAL WORKFLOW ==
    @classmethod
    @with_transaction(manager=None)
    def approve_script(
        cls,
        session,
        *,
        script_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Script'i onaylar.
        
        Args:
            script_id: Script ID'si
            reviewed_by: Onaylayan kullanıcı ID'si
            review_notes: Review notları (opsiyonel)
            
        Returns:
            {"success": True, "approval_status": "APPROVED"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        if script.approval_status == ScriptApprovalStatus.APPROVED:
            raise BusinessRuleViolationError(
                rule_name="already_approved",
                rule_detail=f"Custom script {script_id} is already in APPROVED status",
                message="Script is already approved"
            )
        
        cls._custom_script_repo._update_approval_status(
            session,
            script_id=script_id,
            approval_status=ScriptApprovalStatus.APPROVED,
            reviewed_by=reviewed_by,
            review_notes=review_notes
        )
        
        return {
            "success": True,
            "approval_status": "APPROVED"
        }

    @classmethod
    @with_transaction(manager=None)
    def reject_script(
        cls,
        session,
        *,
        script_id: str,
        reviewed_by: str,
        review_notes: str,
    ) -> Dict[str, Any]:
        """
        Script'i reddeder.
        
        Args:
            script_id: Script ID'si
            reviewed_by: Reddeden kullanıcı ID'si
            review_notes: Red gerekçesi (zorunlu)
            
        Returns:
            {"success": True, "approval_status": "REJECTED"}
        """
        if not review_notes or not review_notes.strip():
            raise InvalidInputError(
                field_name="review_notes",
                message="Review notes are required for rejection"
            )
        
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update_approval_status(
            session,
            script_id=script_id,
            approval_status=ScriptApprovalStatus.REJECTED,
            reviewed_by=reviewed_by,
            review_notes=review_notes
        )
        
        return {
            "success": True,
            "approval_status": "REJECTED"
        }

    @classmethod
    @with_transaction(manager=None)
    def reset_approval_status(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script'in onay durumunu PENDING'e sıfırlar.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "approval_status": "PENDING"}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._update(
            session,
            record_id=script_id,
            approval_status=ScriptApprovalStatus.PENDING,
            reviewed_by=None,
            reviewed_at=None,
            review_notes=None
        )
        
        return {
            "success": True,
            "approval_status": "PENDING"
        }

    # ==================================================================================== DANGEROUS FLAG ==
    @classmethod
    @with_transaction(manager=None)
    def mark_as_dangerous(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script'i tehlikeli olarak işaretler.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "is_dangerous": True}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._mark_as_dangerous(session, script_id=script_id, is_dangerous=True)
        
        return {"success": True, "is_dangerous": True}

    @classmethod
    @with_transaction(manager=None)
    def unmark_as_dangerous(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script'in tehlikeli işaretini kaldırır.
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "is_dangerous": False}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        cls._custom_script_repo._mark_as_dangerous(session, script_id=script_id, is_dangerous=False)
        
        return {"success": True, "is_dangerous": False}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_custom_script(
        cls,
        session,
        *,
        script_id: str,
    ) -> Dict[str, Any]:
        """
        Script'i siler (dosya + veritabanı).
        
        Args:
            script_id: Script ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        script = cls._custom_script_repo._get_by_id(session, record_id=script_id)
        
        if not script:
            raise ResourceNotFoundError(
                resource_name="CustomScript",
                resource_id=script_id
            )
        
        workspace_id = script.workspace_id
        
        # Dosyayı sil
        if script.file_path:
            try:
                delete_file(script.file_path)
            except Exception:
                pass
        
        # Veritabanından sil
        cls._custom_script_repo._delete(session, record_id=script_id)
        
        # Workspace script sayısını güncelle
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if workspace:
            cls._workspace_repo._update(
                session,
                record_id=workspace_id,
                current_custom_script_count=max(0, workspace.current_custom_script_count - 1)
            )
        
        return {
            "success": True,
            "deleted_id": script_id
        }

