from typing import Optional, Dict, List, Any

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class UserRoleService:
    """
    Kullanıcı rolleri servis katmanı.
    
    UserRoles tablosu seed data ile doldurulur ve sistem rolleri değiştirilemez.
    Bu servis rol bilgilerini okuma ve yetki kontrolü için kullanılır.
    """
    _registry = RepositoryRegistry()
    _user_role_repo = _registry.user_roles_repository()

    # ==================================================================================== SEED ==
    @classmethod
    @with_transaction(manager=None)
    def seed_default_user_roles(
        cls,
        session,
        *,
        roles_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Varsayılan kullanıcı rollerini seed eder.
        
        Args:
            roles_data: Rol verilerinin listesi
            
        Returns:
            {"created": int, "skipped": int}
        """
        stats = {"created": 0, "skipped": 0}

        for role_data in roles_data:
            role_name = role_data.get("name")
            if not role_name:
                continue

            existing_role = cls._user_role_repo._get_by_name(session, name=role_name)

            if existing_role:
                stats["skipped"] += 1
            else:
                cls._user_role_repo._create(session, **role_data)
                stats["created"] += 1

        return stats

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_all_user_roles(
        cls,
        session
    ) -> List[Dict[str, Any]]:
        """
        Tüm aktif kullanıcı rollerini getirir.
        
        Returns:
            Rol listesi
        """
        roles = cls._user_role_repo._get_all(session, include_deleted=False)
        return [role.to_dict() for role in roles]

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_role_by_id(
        cls,
        session,
        *,
        role_id: str
    ) -> Dict[str, Any]:
        """
        ID ile kullanıcı rolünü getirir.
        
        Args:
            role_id: Rol ID'si
            
        Returns:
            Rol detayları
            
        Raises:
            ResourceNotFoundError: Rol bulunamazsa
        """
        role = cls._user_role_repo._get_by_id(session, record_id=role_id, raise_not_found=True)
        return role.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_role_by_name(
        cls,
        session,
        *,
        role_name: str
    ) -> Dict[str, Any]:
        """
        İsim ile kullanıcı rolünü getirir.
        
        Args:
            role_name: Rol adı
            
        Returns:
            Rol detayları
            
        Raises:
            ResourceNotFoundError: Rol bulunamazsa
        """
        role = cls._user_role_repo._get_by_name(session, name=role_name)
        if not role:
            raise ResourceNotFoundError(
                resource_name="user_role",
                message=f"Role not found: {role_name}"
            )
        return role.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_role_permissions(
        cls,
        session,
        *,
        role_id: str
    ) -> Dict[str, bool]:
        """
        Belirtilen rolün tüm yetkilerini getirir.
        
        Args:
            role_id: Rol ID'si
            
        Returns:
            Yetki dictionary'si {permission_name: bool}
            
        Raises:
            ResourceNotFoundError: Rol bulunamazsa
        """
        role = cls._user_role_repo._get_by_id(session, record_id=role_id, raise_not_found=True)
        
        # Tüm can_* alanlarını topla
        permissions = {}
        for attr in dir(role):
            if attr.startswith("can_"):
                permissions[attr] = getattr(role, attr, False)
        
        return permissions

    @classmethod
    @with_readonly_session(manager=None)
    def check_permission(
        cls,
        session,
        *,
        role_id: str,
        permission: str
    ) -> bool:
        """
        Belirtilen rolün belirtilen yetkiye sahip olup olmadığını kontrol eder.
        
        Args:
            role_id: Rol ID'si
            permission: Yetki adı (örn: "can_edit_workspace")
            
        Returns:
            True/False
        """
        return cls._user_role_repo._has_permission(
            session, 
            role_id=role_id, 
            permission_field=permission
        )
