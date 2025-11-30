from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, select, update, delete
from datetime import datetime, timezone

from ..base_repository import BaseRepository
from ...models.execution_models.execution_input_model import ExecutionInput


class ExecutionInputRepository(BaseRepository[ExecutionInput]):
    """Repository for managing execution inputs"""
    
    def __init__(self):
        super().__init__(ExecutionInput)

    def _get_by_execution_id(
        self,
        session: Session,
        record_id: str,
        include_deleted: bool = False,
    ) -> List[ExecutionInput]:
        query = select(ExecutionInput).where(ExecutionInput.execution_id == record_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _delete_by_execution_id(
        self,
        session: Session,
        *,
        execution_id: str,
    ):
        """Hard delete all execution inputs for a given execution_id"""
        stmt = delete(ExecutionInput).where(
            ExecutionInput.execution_id == execution_id
        )
        session.execute(stmt)

    def _get_ready_execution_inputs(
        self,
        session: Session,
    ) -> List[ExecutionInput]:
        query = select(ExecutionInput).where(
            and_(
                ExecutionInput.dependency_count == 0,
                ExecutionInput.retry_count < ExecutionInput.max_retries,
                ExecutionInput.is_deleted == False
            )
        ).order_by(
            ExecutionInput.priority.desc(),
            ExecutionInput.wait_factor.desc()
        )
        
        return list(session.execute(query).scalars().all())
    
    def _increment_wait_factor_by_ids(
        self,
        session: Session,
        *,
        execution_input_ids: List[str],
    ) -> int:

        stmt = (
            update(ExecutionInput)
            .where(ExecutionInput.id.in_(execution_input_ids))
            .where(ExecutionInput.is_deleted == False)
            .values(wait_factor=ExecutionInput.wait_factor + 1)
        )
        
        result = session.execute(stmt)
        return result.rowcount

    @BaseRepository._handle_db_exceptions
    def _get_by_execution_and_node(
        self,
        session: Session,
        *,
        execution_id: str,
        node_id: str,
        include_deleted: bool = False,
    ) -> Optional[ExecutionInput]:
        """Get execution input by execution_id and node_id"""
        query = select(ExecutionInput).where(
            ExecutionInput.execution_id == execution_id,
            ExecutionInput.node_id == node_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()