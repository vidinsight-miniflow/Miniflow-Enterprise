from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.workflow_models.edge_model import Edge


class EdgeRepository(BaseRepository[Edge]): 
    def __init__(self):
        super().__init__(Edge)

    @BaseRepository._handle_db_exceptions
    def _get_by_nodes(
        self,
        session: Session,
        *,
        workflow_id: str,
        from_node_id: str,
        to_node_id: str,
        include_deleted: bool = False
    ) -> Optional[Edge]:
        """Get edge by workflow_id, from_node_id and to_node_id"""
        query = select(Edge).where(
            Edge.workflow_id == workflow_id,
            Edge.from_node_id == from_node_id,
            Edge.to_node_id == to_node_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workflow_id(
        self,
        session: Session,
        *,
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Edge]:
        """Get all edges by workflow_id"""
        query = select(Edge).where(Edge.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalars().all()

    @BaseRepository._handle_db_exceptions
    def _get_by_from_node_id(
        self,
        session: Session,
        *,
        workflow_id: str,
        from_node_id: str,
        include_deleted: bool = False
    ) -> List[Edge]:
        """Get all edges where from_node_id matches"""
        query = select(Edge).where(
            Edge.workflow_id == workflow_id,
            Edge.from_node_id == from_node_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())