from typing import Optional, Dict, List, Any

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class WorkspacePlanService:
    """
    Workspace planları servis katmanı.
    
    WorkspacePlans tablosu seed data ile doldurulur ve read-only olarak kullanılır.
    Plan limitleri ve özellikleri bu servis üzerinden okunur.
    """
    _registry = RepositoryRegistry()
    _workspace_plan_repo = _registry.workspace_plans_repository()

    # ==================================================================================== SEED ==
    @classmethod
    @with_transaction(manager=None)
    def seed_default_workspace_plans(
        cls,
        session,
        *,
        plans_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Varsayılan workspace planlarını seed eder.
        
        Args:
            plans_data: Plan verilerinin listesi
            
        Returns:
            {"created": int, "skipped": int}
        """
        stats = {"created": 0, "skipped": 0}

        for plan_data in plans_data:
            plan_name = plan_data.get("name")
            if not plan_name:
                continue

            existing_plan = cls._workspace_plan_repo._get_by_name(session, name=plan_name)

            if existing_plan:
                stats["skipped"] += 1
            else:
                cls._workspace_plan_repo._create(session, **plan_data)
                stats["created"] += 1

        return stats

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_all_workspace_plans(
        cls,
        session
    ) -> List[Dict[str, Any]]:
        """
        Tüm aktif workspace planlarını getirir.
        
        Returns:
            Plan listesi (display_order'a göre sıralı)
        """
        plans = cls._workspace_plan_repo._get_all(session, include_deleted=False)
        plan_list = [plan.to_dict() for plan in plans]
        return sorted(plan_list, key=lambda x: x.get("display_order", 0))

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_plan_by_id(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, Any]:
        """
        ID ile workspace planını getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            Plan detayları
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        plan = cls._workspace_plan_repo._get_by_id(session, record_id=plan_id, raise_not_found=True)
        return plan.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_plan_by_name(
        cls,
        session,
        *,
        plan_name: str
    ) -> Dict[str, Any]:
        """
        İsim ile workspace planını getirir.
        
        Args:
            plan_name: Plan adı
            
        Returns:
            Plan detayları
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        plan = cls._workspace_plan_repo._get_by_name(session, name=plan_name)
        if not plan:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_name}"
            )
        return plan.to_dict()

    # ==================================================================================== LIMITS ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_limits(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, Optional[int]]:
        """
        Planın workspace limitlerini getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            {
                "max_members_per_workspace": int,
                "max_workflows_per_workspace": int,
                "max_custom_scripts_per_workspace": int,
                "storage_limit_mb_per_workspace": int,
                "max_file_size_mb_per_workspace": int
            }
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        limits = cls._workspace_plan_repo._get_limits(session, plan_id=plan_id)
        if limits is None:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_id}"
            )
        return limits

    @classmethod
    @with_readonly_session(manager=None)
    def get_monthly_limits(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, Optional[int]]:
        """
        Planın aylık execution limitlerini getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            {
                "monthly_execution_limit": int,
                "max_concurrent_executions": int
            }
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        limits = cls._workspace_plan_repo._get_monthly_limits(session, plan_id=plan_id)
        if limits is None:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_id}"
            )
        return limits

    @classmethod
    @with_readonly_session(manager=None)
    def get_feature_flags(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, bool]:
        """
        Planın özellik flag'lerini getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            {
                "can_use_custom_scripts": bool,
                "can_use_api_access": bool,
                "can_use_webhooks": bool,
                "can_use_scheduling": bool,
                "can_export_data": bool
            }
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        features = cls._workspace_plan_repo._get_feature_limits(session, plan_id=plan_id)
        if features is None:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_id}"
            )
        return features

    @classmethod
    @with_readonly_session(manager=None)
    def get_api_limits(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, Optional[int]]:
        """
        Planın API rate limitlerini getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            {
                "max_api_keys_per_workspace": int,
                "api_rate_limit_per_minute": int,
                "api_rate_limit_per_hour": int,
                "api_rate_limit_per_day": int
            }
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        limits = cls._workspace_plan_repo._get_api_limits(session, plan_id=plan_id)
        if limits is None:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_id}"
            )
        return limits

    @classmethod
    @with_readonly_session(manager=None)
    def get_pricing(
        cls,
        session,
        *,
        plan_id: str
    ) -> Dict[str, Optional[float]]:
        """
        Planın fiyatlandırma bilgilerini getirir.
        
        Args:
            plan_id: Plan ID'si
            
        Returns:
            {
                "monthly_price_usd": float,
                "yearly_price_usd": float,
                "price_per_extra_member_usd": float,
                "price_per_extra_workflow_usd": float
            }
            
        Raises:
            ResourceNotFoundError: Plan bulunamazsa
        """
        pricing = cls._workspace_plan_repo._get_pricing(session, plan_id=plan_id)
        if pricing is None:
            raise ResourceNotFoundError(
                resource_name="workspace_plan",
                message=f"Plan not found: {plan_id}"
            )
        return pricing

    @classmethod
    @with_readonly_session(manager=None)
    def get_all_api_rate_limits(
        cls,
        session
    ) -> Dict[str, Dict[str, int]]:
        """
        Tüm planların API rate limitlerini döndürür.
        Rate limiting middleware için kullanılır.
        
        Returns:
            {plan_id: {"minute": int, "hour": int, "day": int}}
        """
        plans = cls._workspace_plan_repo._get_all(session, include_deleted=False)
        
        limits_dict = {}
        for plan in plans:
            limits = {}
            if plan.api_rate_limit_per_minute is not None:
                limits["minute"] = plan.api_rate_limit_per_minute
            if plan.api_rate_limit_per_hour is not None:
                limits["hour"] = plan.api_rate_limit_per_hour
            if plan.api_rate_limit_per_day is not None:
                limits["day"] = plan.api_rate_limit_per_day
            
            limits_dict[plan.id] = limits
        
        return limits_dict
