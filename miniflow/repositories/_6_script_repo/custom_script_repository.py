from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy import and_

from ..base_repository import BaseRepository
from miniflow.models import CustomScript
from miniflow.models.enums import ScriptApprovalStatus, ScriptTestStatus


class CustomScriptRepository(BaseRepository[CustomScript]): 
    def __init__(self):
        super().__init__(CustomScript)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[CustomScript]:
        """Get custom script by workspace_id and name"""
        query = select(CustomScript).where(
            CustomScript.workspace_id == workspace_id,
            CustomScript.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[CustomScript]:
        """Get all custom scripts by workspace_id"""
        query = select(CustomScript).where(CustomScript.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count custom scripts by workspace_id"""
        query = select(func.count(CustomScript.id)).where(CustomScript.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_approval_status(
        self,
        session: Session,
        *,
        workspace_id: str,
        approval_status: ScriptApprovalStatus,
        include_deleted: bool = False
    ) -> List[CustomScript]:
        """Get custom scripts by approval status"""
        query = select(CustomScript).where(
            CustomScript.workspace_id == workspace_id,
            CustomScript.approval_status == approval_status
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_category(
        self,
        session: Session,
        *,
        workspace_id: str,
        category: str,
        include_deleted: bool = False
    ) -> List[CustomScript]:
        """Get custom scripts by category"""
        query = select(CustomScript).where(
            CustomScript.workspace_id == workspace_id,
            CustomScript.category == category
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _update_approval_status(
        self,
        session: Session,
        *,
        script_id: str,
        approval_status: ScriptApprovalStatus,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> Optional[CustomScript]:
        """Update approval status"""
        script = self._get_by_id(session, record_id=script_id)
        if script:
            script.approval_status = approval_status
            script.reviewed_by = reviewed_by
            script.reviewed_at = datetime.now(timezone.utc)
            script.review_notes = review_notes
            return script
        return None

    @BaseRepository._handle_db_exceptions
    def _update_test_status(
        self,
        session: Session,
        *,
        script_id: str,
        test_status: ScriptTestStatus,
        test_results: Optional[dict] = None,
        test_coverage: Optional[float] = None
    ) -> Optional[CustomScript]:
        """Update test status"""
        script = self._get_by_id(session, record_id=script_id)
        if script:
            script.test_status = test_status
            if test_results is not None:
                script.test_results = test_results
            if test_coverage is not None:
                script.test_coverage = test_coverage
            return script
        return None

    @BaseRepository._handle_db_exceptions
    def _mark_as_dangerous(
        self,
        session: Session,
        script_id: str,
        is_dangerous: bool = True
    ) -> None:
        """Mark script as dangerous"""
        script = self._get_by_id(session, record_id=script_id)
        if script:
            script.is_dangerous = is_dangerous