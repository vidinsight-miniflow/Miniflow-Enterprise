from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
)
from miniflow.utils.helpers.file_helper import (
    get_workspace_file_path,
    get_workspace_custom_script_path,
    get_workspace_temp_path,
    delete_folder,
)


class WorkspaceManagementService:
    """
    Workspace yönetim servisi.
    
    Workspace oluşturma, güncelleme, silme ve detay işlemlerini yönetir.
    NOT: user_exists ve workspace_exists kontrolleri middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _workspace_repo = _registry.workspace_repository()
    _workspace_member_repo = _registry.workspace_member_repository()
    _workspace_invitation_repo = _registry.workspace_invitation_repository()
    _workspace_plan_repo = _registry.workspace_plans_repository()
    _user_roles_repo = _registry.user_roles_repository()
    _user_repo = _registry.user_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_workspace(
        cls,
        session,
        *,
        name: str,
        slug: str,
        owner_id: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Yeni workspace oluşturur.
        
        - Varsayılan olarak "Freemium" plan ile oluşturulur
        - Owner otomatik olarak member olarak eklenir
        - Kullanıcının free workspace limiti kontrol edilir
        
        Args:
            name: Workspace adı
            slug: URL-friendly benzersiz slug
            owner_id: Sahip kullanıcı ID'si
            description: Açıklama (opsiyonel)
            
        Returns:
            Oluşturulan workspace bilgileri
            
        Raises:
            ResourceAlreadyExistsError: Name veya slug zaten mevcut
            BusinessRuleViolationError: Free workspace limiti aşıldı
        """
        # Benzersizlik kontrolleri
        if cls._workspace_repo._get_by_slug(session, slug=slug):
            raise ResourceAlreadyExistsError(
                resource_name="Workspace",
                conflicting_field="slug",
                message=f"Workspace with slug '{slug}' already exists"
            )
        
        if cls._workspace_repo._get_by_name(session, name=name):
            raise ResourceAlreadyExistsError(
                resource_name="Workspace",
                conflicting_field="name",
                message=f"Workspace with name '{name}' already exists"
            )
        
        # Kullanıcıyı al
        user = cls._user_repo._get_by_id(session, record_id=owner_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=owner_id
            )
        
        # Free workspace limiti kontrolü
        if user.current_free_workspace_count >= 1:
            raise BusinessRuleViolationError(
                rule_name="free_workspace_limit_reached",
                rule_detail="Free plan allows only 1 workspace",
                message="You can only have 1 free workspace. Please upgrade to create more."
            )
        
        # Freemium planı al
        plan = cls._workspace_plan_repo._get_by_name(session, name="Freemium")
        if not plan:
            raise BusinessRuleViolationError(
                rule_name="plan_not_found",
                rule_detail="Freemium plan is required for workspace creation but not found",
                message="Freemium plan not found in system"
            )
        
        # Owner rolünü al
        owner_role = cls._user_roles_repo._get_by_name(session, name="Owner")
        if not owner_role:
            raise BusinessRuleViolationError(
                rule_name="role_not_found",
                rule_detail="Owner role is required for workspace creation but not found",
                message="Owner role not found in system"
            )
        
        # Workspace oluştur
        workspace = cls._workspace_repo._create(
            session,
            name=name,
            slug=slug,
            description=description,
            owner_id=owner_id,
            plan_id=plan.id,
            member_limit=plan.max_members_per_workspace,
            current_member_count=1,
            workflow_limit=plan.max_workflows_per_workspace,
            current_workflow_count=0,
            custom_script_limit=plan.max_custom_scripts_per_workspace or 0,
            current_custom_script_count=0,
            max_file_size_mb_per_workspace=plan.max_file_size_mb_per_workspace,
            storage_limit_mb=plan.storage_limit_mb_per_workspace,
            current_storage_mb=0,
            api_key_limit=plan.max_api_keys_per_workspace or 0,
            current_api_key_count=0,
            monthly_execution_limit=plan.monthly_execution_limit,
            current_month_executions=0,
            monthly_concurrent_executions=plan.max_concurrent_executions,
            current_month_concurrent_executions=0,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            created_by=owner_id
        )
        
        # Owner'ı member olarak ekle
        cls._workspace_member_repo._create(
            session,
            workspace_id=workspace.id,
            user_id=owner_id,
            role_id=owner_role.id,
            role_name=owner_role.name,
            invited_by=owner_id,
            joined_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            custom_permissions=None,
            created_by=owner_id
        )
        
        # Kullanıcı workspace sayılarını güncelle
        cls._user_repo._update(
            session,
            record_id=owner_id,
            current_workspace_count=user.current_workspace_count + 1,
            current_free_workspace_count=user.current_free_workspace_count + 1
        )
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "plan_id": workspace.plan_id
        }

    # ==================================================================================== VALIDATE ==
    @classmethod
    @with_readonly_session(manager=None)
    def validate_workspace(
        cls,
        session,
        *,
        workspace_id: str,
        check_suspended: bool = True,
    ) -> bool:
        """
        Workspace'in var olup olmadığını ve askıya alınmış olup olmadığını doğrular.
        
        Args:
            workspace_id: Workspace ID'si
            check_suspended: Askıya alınmış workspace'leri kontrol et (default: True)
            
        Returns:
            True (workspace geçerli ise)
            
        Raises:
            ResourceNotFoundError: Workspace bulunamadı
            BusinessRuleViolationError: Workspace askıya alınmış
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        if check_suspended and workspace.is_suspended:
            raise BusinessRuleViolationError(
                rule_name="workspace_suspended",
                rule_detail=f"Workspace {workspace_id} is suspended: {workspace.suspension_reason or 'No reason provided'}",
                message=f"Workspace is suspended: {workspace.suspension_reason or 'No reason provided'}"
            )
        
        return True

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace bilgilerini getirir (basit format).
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            Workspace bilgileri (owner_id dahil)
            
        Raises:
            ResourceNotFoundError: Workspace bulunamadı
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "owner_id": workspace.owner_id,
            "plan_id": workspace.plan_id,
            "is_suspended": workspace.is_suspended,
        }

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_details(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace detaylarını getirir.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            Workspace detayları
            
        Raises:
            ResourceNotFoundError: Workspace bulunamadı
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "owner_name": workspace.owner.name if workspace.owner else None,
            "owner_email": workspace.owner.email if workspace.owner else None,
            "plan_id": workspace.plan_id,
            "is_suspended": workspace.is_suspended,
            "suspension_reason": workspace.suspension_reason,
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_limits(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace limitlerini ve mevcut kullanımı getirir.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            Limit ve kullanım bilgileri
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        return {
            "members": {
                "limit": workspace.member_limit,
                "current": workspace.current_member_count,
                "available": workspace.member_limit - workspace.current_member_count
            },
            "workflows": {
                "limit": workspace.workflow_limit,
                "current": workspace.current_workflow_count,
                "available": workspace.workflow_limit - workspace.current_workflow_count
            },
            "custom_scripts": {
                "limit": workspace.custom_script_limit,
                "current": workspace.current_custom_script_count,
                "available": workspace.custom_script_limit - workspace.current_custom_script_count if workspace.custom_script_limit > 0 else -1
            },
            "storage_mb": {
                "limit": workspace.storage_limit_mb,
                "current": workspace.current_storage_mb,
                "available": workspace.storage_limit_mb - workspace.current_storage_mb
            },
            "api_keys": {
                "limit": workspace.api_key_limit,
                "current": workspace.current_api_key_count,
                "available": workspace.api_key_limit - workspace.current_api_key_count if workspace.api_key_limit > 0 else -1
            },
            "monthly_executions": {
                "limit": workspace.monthly_execution_limit,
                "current": workspace.current_month_executions,
                "available": workspace.monthly_execution_limit - workspace.current_month_executions
            },
            "concurrent_executions": {
                "limit": workspace.monthly_concurrent_executions,
                "current": workspace.current_month_concurrent_executions
            },
            "billing_period": {
                "start": workspace.current_period_start.isoformat() if workspace.current_period_start else None,
                "end": workspace.current_period_end.isoformat() if workspace.current_period_end else None
            },
            "max_file_size_mb": workspace.max_file_size_mb_per_workspace
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_by_slug(
        cls,
        session,
        *,
        slug: str,
    ) -> Dict[str, Any]:
        """
        Slug ile workspace detaylarını getirir.
        
        Args:
            slug: Workspace slug'ı
            
        Returns:
            Workspace detayları
        """
        workspace = cls._workspace_repo._get_by_slug(session, slug=slug)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=slug
            )
        
        return {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "description": workspace.description,
            "owner_id": workspace.owner_id,
            "plan_id": workspace.plan_id,
            "is_suspended": workspace.is_suspended
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_workspace(
        cls,
        session,
        *,
        workspace_id: str,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace bilgilerini günceller.
        
        Args:
            workspace_id: Workspace ID'si
            name: Yeni ad (opsiyonel)
            slug: Yeni slug (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            
        Returns:
            Güncellenmiş workspace bilgileri
            
        Raises:
            ResourceAlreadyExistsError: Name veya slug zaten mevcut
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        update_data = {}
        
        if name is not None and name != workspace.name:
            existing = cls._workspace_repo._get_by_name(session, name=name)
            if existing:
                raise ResourceAlreadyExistsError(
                    resource_name="Workspace",
                    conflicting_field="name",
                    message=f"Workspace with name '{name}' already exists"
                )
            update_data["name"] = name
        
        if slug is not None and slug != workspace.slug:
            existing = cls._workspace_repo._get_by_slug(session, slug=slug)
            if existing:
                raise ResourceAlreadyExistsError(
                    resource_name="Workspace",
                    conflicting_field="slug",
                    message=f"Workspace with slug '{slug}' already exists"
                )
            update_data["slug"] = slug
        
        if description is not None:
            update_data["description"] = description
        
        if update_data:
            cls._workspace_repo._update(session, record_id=workspace_id, **update_data)
        
        # Güncel workspace'i al
        updated_workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        
        return {
            "id": updated_workspace.id,
            "name": updated_workspace.name,
            "slug": updated_workspace.slug,
            "description": updated_workspace.description
        }

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_workspace(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'i ve tüm ilişkili verileri siler.
        
        - Tüm üyeler silinir
        - Tüm davetler silinir
        - Dosya sistemi temizlenir
        - Owner'ın workspace sayıları güncellenir
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            Silme özeti
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        owner_id = workspace.owner_id
        is_free_workspace = workspace.plan_id is not None  # Freemium plan kontrolü yapılabilir
        
        # Üyeleri sil
        deleted_members = cls._workspace_member_repo._delete_all_by_workspace_id(session, workspace_id=workspace_id)
        
        # Davetleri sil
        deleted_invitations = cls._workspace_invitation_repo._delete_all_by_workspace_id(session, workspace_id=workspace_id)
        
        # Owner'ın workspace sayılarını güncelle
        user = cls._user_repo._get_by_id(session, record_id=owner_id)
        if user:
            new_workspace_count = max(0, user.current_workspace_count - 1)
            new_free_count = max(0, user.current_free_workspace_count - 1)
            cls._user_repo._update(
                session,
                record_id=owner_id,
                current_workspace_count=new_workspace_count,
                current_free_workspace_count=new_free_count
            )
        
        # Workspace'i sil
        cls._workspace_repo._delete(session, record_id=workspace_id)
        
        # Dosya sistemini temizle
        try:
            files_path = get_workspace_file_path(workspace_id)
            delete_folder(files_path)
        except Exception:
            pass
        
        try:
            scripts_path = get_workspace_custom_script_path(workspace_id)
            delete_folder(scripts_path)
        except Exception:
            pass
        
        try:
            temp_path = get_workspace_temp_path(workspace_id)
            delete_folder(temp_path)
        except Exception:
            pass
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "deleted_members": deleted_members,
            "deleted_invitations": deleted_invitations
        }

    # ==================================================================================== SUSPEND ==
    @classmethod
    @with_transaction(manager=None)
    def suspend_workspace(
        cls,
        session,
        *,
        workspace_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Workspace'i askıya alır.
        
        Args:
            workspace_id: Workspace ID'si
            reason: Askıya alma nedeni
            
        Returns:
            {"success": True, "suspended_at": str}
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        if workspace.is_suspended:
            raise BusinessRuleViolationError(
                rule_name="already_suspended",
                rule_detail=f"Workspace {workspace_id} is already suspended",
                message="Workspace is already suspended"
            )
        
        cls._workspace_repo._suspend_workspace(session, workspace_id=workspace_id, reason=reason)
        
        return {
            "success": True,
            "suspended_at": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    @with_transaction(manager=None)
    def unsuspend_workspace(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace askıya almayı kaldırır.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"success": True}
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        if not workspace.is_suspended:
            raise BusinessRuleViolationError(
                rule_name="not_suspended",
                rule_detail=f"Workspace {workspace_id} is not suspended",
                message="Workspace is not suspended"
            )
        
        cls._workspace_repo._unsuspend_workspace(session, workspace_id=workspace_id)
        
        return {"success": True}

    # ==================================================================================== TRANSFER OWNERSHIP ==
    @classmethod
    @with_transaction(manager=None)
    def transfer_ownership(
        cls,
        session,
        *,
        workspace_id: str,
        current_owner_id: str,
        new_owner_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace sahipliğini başka bir kullanıcıya transfer eder.
        
        Args:
            workspace_id: Workspace ID'si
            current_owner_id: Mevcut sahip ID'si
            new_owner_id: Yeni sahip ID'si
            
        Returns:
            Transfer sonucu
            
        Raises:
            BusinessRuleViolationError: Yetki hatası, kullanıcı üye değil
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        if workspace.owner_id != current_owner_id:
            raise BusinessRuleViolationError(
                rule_name="not_owner",
                rule_detail=f"User {current_user_id} is not the owner of workspace {workspace_id}",
                message="Only the current owner can transfer ownership"
            )
        
        # Yeni owner'ın üye olduğunu kontrol et
        new_owner_member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=new_owner_id
        )
        if not new_owner_member:
            raise BusinessRuleViolationError(
                rule_name="user_not_member",
                rule_detail=f"User {new_owner_id} is not a member of workspace {workspace_id}",
                message="New owner must be an existing member of the workspace"
            )
        
        # Owner rolünü al
        owner_role = cls._user_roles_repo._get_by_name(session, name="Owner")
        admin_role = cls._user_roles_repo._get_by_name(session, name="Admin")
        
        if not owner_role or not admin_role:
            raise BusinessRuleViolationError(
                rule_name="roles_not_found",
                rule_detail="Owner and Admin roles are required but not found in system",
                message="Required roles not found in system"
            )
        
        # Eski owner'ı admin yap
        current_owner_member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=current_owner_id
        )
        if current_owner_member:
            cls._workspace_member_repo._update_role(
                session,
                member_id=current_owner_member.id,
                role_id=admin_role.id,
                role_name=admin_role.name
            )
        
        # Yeni owner'ı owner yap
        cls._workspace_member_repo._update_role(
            session,
            member_id=new_owner_member.id,
            role_id=owner_role.id,
            role_name=owner_role.name
        )
        
        # Workspace owner'ını güncelle
        cls._workspace_repo._update(session, record_id=workspace_id, owner_id=new_owner_id)
        
        # Kullanıcıların workspace sayılarını güncelle
        current_owner = cls._user_repo._get_by_id(session, record_id=current_owner_id)
        new_owner = cls._user_repo._get_by_id(session, record_id=new_owner_id)
        
        if current_owner:
            cls._user_repo._update(
                session,
                record_id=current_owner_id,
                current_workspace_count=max(0, current_owner.current_workspace_count - 1),
                current_free_workspace_count=max(0, current_owner.current_free_workspace_count - 1)
            )
        
        if new_owner:
            cls._user_repo._update(
                session,
                record_id=new_owner_id,
                current_workspace_count=new_owner.current_workspace_count + 1,
                current_free_workspace_count=new_owner.current_free_workspace_count + 1
            )
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "previous_owner_id": current_owner_id,
            "new_owner_id": new_owner_id
        }

