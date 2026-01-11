from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, select, update, delete, func

from ..base_repository import BaseRepository
from miniflow.models import ExecutionOutput


class ExecutionOutputRepository(BaseRepository[ExecutionOutput]):
    """Repository for managing execution outputs"""
    
    def __init__(self):
        super().__init__(ExecutionOutput)

    @BaseRepository._handle_db_exceptions
    def _get_by_execution_id(
        self,
        session: Session,
        record_id: str,
        include_deleted: bool = False,
    ) -> List[ExecutionOutput]:
        query = select(ExecutionOutput).where(ExecutionOutput.execution_id == record_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_execution_and_node(
        self,
        session: Session,
        *,
        execution_id: str,
        node_id: str,
        include_deleted: bool = False,
    ) -> Optional[ExecutionOutput]:
        """Get execution output by execution_id and node_id."""
        query = select(ExecutionOutput).where(
            ExecutionOutput.execution_id == execution_id,
            ExecutionOutput.node_id == node_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _delete_by_execution_id(
        self,
        session: Session,
        *,
        execution_id: str,
    ):
        """Hard delete all execution outputs for a given execution_id"""
        stmt = delete(ExecutionOutput).where(
            ExecutionOutput.execution_id == execution_id
        )
        session.execute(stmt)

    @BaseRepository._handle_db_exceptions
    def _count_by_execution_id(
        self,
        session: Session,
        execution_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count outputs by execution_id"""
        query = select(func.count(ExecutionOutput.id)).where(
            ExecutionOutput.execution_id == execution_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _count_by_status(
        self,
        session: Session,
        *,
        execution_id: str,
        status: str,
        include_deleted: bool = False
    ) -> int:
        """Count outputs by execution_id and status"""
        query = select(func.count(ExecutionOutput.id)).where(
            ExecutionOutput.execution_id == execution_id,
            ExecutionOutput.status == status
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_status(
        self,
        session: Session,
        *,
        execution_id: str,
        status: str,
        include_deleted: bool = False
    ) -> List[ExecutionOutput]:
        """Get outputs by execution_id and status"""
        query = select(ExecutionOutput).where(
            ExecutionOutput.execution_id == execution_id,
            ExecutionOutput.status == status
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _update_status(
        self,
        session: Session,
        *,
        output_id: str,
        status: str,
        ended_at: Optional[datetime] = None,
        result_data: Optional[dict] = None,
        error_message: Optional[str] = None,
        error_details: Optional[dict] = None
    ) -> Optional[ExecutionOutput]:
        """Update output status and results"""
        output = self._get_by_id(session, record_id=output_id)
        if output:
            output.status = status
            if ended_at is not None:
                output.ended_at = ended_at
            if result_data is not None:
                output.result_data = result_data
            if error_message is not None:
                output.error_message = error_message
            if error_details is not None:
                output.error_details = error_details
            return output
        return None