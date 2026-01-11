from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, select, update, delete, func
from datetime import datetime, timezone

from ..base_repository import BaseRepository
from miniflow.models import ExecutionInput


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

    @BaseRepository._handle_db_exceptions
    def _delete_by_ids(
        self,
        session: Session,
        *,
        execution_input_ids: List[str],
    ) -> int:
        if not execution_input_ids:
            return 0
        
        stmt = delete(ExecutionInput).where(
            ExecutionInput.id.in_(execution_input_ids)
        )
        
        result = session.execute(stmt)
        return result.rowcount

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
    
    @BaseRepository._handle_db_exceptions
    def _get_by_execution_and_node_ids(
        self,
        session: Session,
        *,
        execution_id: str,
        node_ids: List[str],
        include_deleted: bool = False,
    ) -> List[ExecutionInput]:
        """
        Batch get execution inputs by execution_id and multiple node_ids.
        Optimizes N+1 query problem by fetching all inputs in a single query.
        
        Args:
            session: Database session
            execution_id: Execution ID
            node_ids: List of node IDs to fetch
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of ExecutionInput objects matching the criteria
        """
        if not node_ids:
            return []
        
        query = select(ExecutionInput).where(
            ExecutionInput.execution_id == execution_id,
            ExecutionInput.node_id.in_(node_ids)
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())
    
    @BaseRepository._handle_db_exceptions
    def _decrement_dependency_count_by_node_ids(
        self,
        session: Session,
        *,
        execution_id: str,
        node_ids: List[str],
    ) -> int:
        """
        Batch decrement dependency_count for execution inputs by node_ids.
        Only decrements if dependency_count > 0 (prevents negative values).
        Optimizes N+1 update problem by updating all inputs in a single query.
        
        Args:
            session: Database session
            execution_id: Execution ID
            node_ids: List of node IDs whose dependency_count should be decremented
            
        Returns:
            Number of rows updated
        """
        if not node_ids:
            return 0
        
        stmt = (
            update(ExecutionInput)
            .where(
                ExecutionInput.execution_id == execution_id,
                ExecutionInput.node_id.in_(node_ids),
                ExecutionInput.is_deleted == False,
                ExecutionInput.dependency_count > 0  # Only decrement if > 0
            )
            .values(dependency_count=ExecutionInput.dependency_count - 1)
        )
        
        result = session.execute(stmt)
        return result.rowcount