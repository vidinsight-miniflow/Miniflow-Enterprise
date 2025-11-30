from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, select, update, delete

from ..base_repository import BaseRepository
from ...models.execution_models.execution_output_model import ExecutionOutput


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