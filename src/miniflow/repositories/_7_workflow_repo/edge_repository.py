from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Edge


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
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Edge]:
        """Get all edges by workflow_id"""
        query = select(Edge).where(Edge.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workflow_id(
        self,
        session: Session,
        workflow_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count edges by workflow_id"""
        query = select(func.count(Edge.id)).where(Edge.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

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

    @BaseRepository._handle_db_exceptions
    def _get_by_to_node_id(
        self,
        session: Session,
        *,
        workflow_id: str,
        to_node_id: str,
        include_deleted: bool = False
    ) -> List[Edge]:
        """Get all edges where to_node_id matches"""
        query = select(Edge).where(
            Edge.workflow_id == workflow_id,
            Edge.to_node_id == to_node_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _delete_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str
    ) -> int:
        """Delete all edges by workflow_id"""
        edges = self._get_all_by_workflow_id(session, workflow_id=workflow_id)
        count = len(edges)
        for edge in edges:
            self._delete(session, record_id=edge.id)
        return count

    @BaseRepository._handle_db_exceptions
    def _delete_edges_by_node_id(
        self,
        session: Session,
        node_id: str
    ) -> int:
        """Delete all edges connected to a node (incoming and outgoing)"""
        # Get both incoming and outgoing edges
        query = select(Edge).where(
            (Edge.from_node_id == node_id) | (Edge.to_node_id == node_id)
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        edges = list(session.execute(query).scalars().all())
        
        count = len(edges)
        for edge in edges:
            self._delete(session, record_id=edge.id)
        return count

    @BaseRepository._handle_db_exceptions
    def _get_outgoing_edges(
        self,
        session: Session,
        from_node_id: str,
        include_deleted: bool = False
    ) -> List[Edge]:
        """Get all outgoing edges from a node (without workflow_id filter)"""
        query = select(Edge).where(Edge.from_node_id == from_node_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())