from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Trigger
from miniflow.models.enums import TriggerType


class TriggerRepository(BaseRepository[Trigger]):    
    def __init__(self):
        super().__init__(Trigger)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Trigger]:
        """Get trigger by workspace_id and name"""
        query = select(Trigger).where(
            Trigger.workspace_id == workspace_id,
            Trigger.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Trigger]:
        """Get all triggers by workspace_id"""
        query = select(Trigger).where(Trigger.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Trigger]:
        """Get all triggers by workflow_id"""
        query = select(Trigger).where(Trigger.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count triggers by workspace_id"""
        query = select(func.count(Trigger.id)).where(Trigger.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_enabled_triggers(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Trigger]:
        """Get enabled triggers for a workspace"""
        query = select(Trigger).where(
            Trigger.workspace_id == workspace_id,
            Trigger.is_enabled == True
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_type(
        self,
        session: Session,
        *,
        workspace_id: str,
        trigger_type: TriggerType,
        include_deleted: bool = False
    ) -> List[Trigger]:
        """Get triggers by type"""
        query = select(Trigger).where(
            Trigger.workspace_id == workspace_id,
            Trigger.trigger_type == trigger_type
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _delete_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str
    ) -> int:
        """Delete all triggers by workflow_id"""
        triggers = self._get_all_by_workflow_id(session, workflow_id=workflow_id)
        count = len(triggers)
        for trigger in triggers:
            self._delete(session, record_id=trigger.id)
        return count