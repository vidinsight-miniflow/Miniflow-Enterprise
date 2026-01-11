from typing import Optional, Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..base_repository import BaseRepository
from miniflow.models import WorkspacePlans


class WorkspacePlansRepository(BaseRepository[WorkspacePlans]):
    def __init__(self):
        super().__init__(WorkspacePlans)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(self, session: Session, name: str) -> Optional[WorkspacePlans]:
        if not name:
            return None 
        
        query = select(self.model).where(self.model.name == name)
        result = session.execute(query)
        return result.scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _get_monthly_limits(self, session: Session, plan_id: str) -> Optional[Dict[str, Optional[int]]]:
        plan = self._get_by_id(session, record_id=plan_id, raise_not_found=False)
        if not plan:
            return None
        
        return {
            "monthly_execution_limit": plan.monthly_execution_limit,
            "max_concurrent_executions": plan.max_concurrent_executions
        }

    @BaseRepository._handle_db_exceptions
    def _get_limits(self, session: Session, plan_id: str) -> Optional[Dict[str, Optional[int]]]:
        plan = self._get_by_id(session, record_id=plan_id, raise_not_found=False)
        if not plan:
            return None
        
        return {
            "max_members_per_workspace": plan.max_members_per_workspace,
            "max_workflows_per_workspace": plan.max_workflows_per_workspace,
            "max_custom_scripts_per_workspace": plan.max_custom_scripts_per_workspace,
            "storage_limit_mb_per_workspace": plan.storage_limit_mb_per_workspace,
            "max_file_size_mb_per_workspace": plan.max_file_size_mb_per_workspace
        }
    
    @BaseRepository._handle_db_exceptions
    def _get_feature_limits(self, session: Session, plan_id: str) -> Optional[Dict[str, bool]]:
        plan = self._get_by_id(session, record_id=plan_id, raise_not_found=False)
        if not plan:
            return None
        
        return {
            "can_use_custom_scripts": plan.can_use_custom_scripts,
            "can_use_api_access": plan.can_use_api_access,
            "can_use_webhooks": plan.can_use_webhooks,
            "can_use_scheduling": plan.can_use_scheduling,
            "can_export_data": plan.can_export_data
        }

    @BaseRepository._handle_db_exceptions
    def _get_api_limits(self, session: Session, plan_id: str) -> Optional[Dict[str, Optional[int]]]:
        plan = self._get_by_id(session, record_id=plan_id, raise_not_found=False)
        if not plan:
            return None
        
        return {
            "max_api_keys_per_workspace": plan.max_api_keys_per_workspace,
            "api_rate_limit_per_minute": plan.api_rate_limit_per_minute,
            "api_rate_limit_per_hour": plan.api_rate_limit_per_hour,
            "api_rate_limit_per_day": plan.api_rate_limit_per_day
        }

    @BaseRepository._handle_db_exceptions
    def _get_pricing(self, session: Session, plan_id: str) -> Optional[Dict[str, Optional[float]]]:
        plan = self._get_by_id(session, record_id=plan_id, raise_not_found=False)
        if not plan:
            return None
        
        return {
            "monthly_price_usd": plan.monthly_price_usd,
            "yearly_price_usd": plan.yearly_price_usd,
            "price_per_extra_member_usd": plan.price_per_extra_member_usd,
            "price_per_extra_workflow_usd": plan.price_per_extra_workflow_usd
        }