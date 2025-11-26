from typing import Optional, Dict, List, Any

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)


class WorkspacePlansService:

    def __init__(self):
        self._registry = RepositoryRegistry()
        self.workspace_plans_repository = self._registry.workspace_plans_repository
        self._workspace_repo = self._registry.workspace_repository

    @with_transaction(manager=None)
    def seed_plan(self, session, *, plans_data: List[Dict]):
        """Seed plans (legacy method for backward compatibility)"""
        stats = {"created": 0, "skipped": 0, "updated": 0}

        for plan_data in plans_data:
            plan_name = plan_data.get("name")
            if not plan_name:
                continue

            existing_plan = self.workspace_plans_repository._get_by_name(session, name=plan_name)

            if existing_plan:
                stats["skipped"] += 1
            else:
                self.workspace_plans_repository._create(session, **plan_data)
                stats["created"] += 1

        return stats

    @with_readonly_session(manager=None)
    def get_api_limits(self, session) -> Dict[str, Dict[str, Any]]:
        """
        Tüm planların API rate limitlerini döndürür.
        Returns: {plan_id: {"limits": {"minute": int, "hour": int, "day": int}}}
        """
        from sqlalchemy import select
        from ...database.models.info_models.workspace_plans_model import WorkspacePlans
        
        query = select(WorkspacePlans)
        result = session.execute(query)
        plans = result.scalars().all()
        
        limits_dict = {}
        for plan in plans:
            limits = {}
            if plan.api_rate_limit_per_minute is not None:
                limits["minute"] = plan.api_rate_limit_per_minute
            if plan.api_rate_limit_per_hour is not None:
                limits["hour"] = plan.api_rate_limit_per_hour
            if plan.api_rate_limit_per_day is not None:
                limits["day"] = plan.api_rate_limit_per_day
            
            limits_dict[plan.id] = {"limits": limits}
        
        return limits_dict