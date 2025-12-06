from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Node


class NodeRepository(BaseRepository[Node]):    
    def __init__(self):
        super().__init__(Node)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workflow_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Node]:
        """Get node by workflow_id and name"""
        query = select(Node).where(
            Node.workflow_id == workflow_id,
            Node.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _get_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Node]:
        """Get all nodes by workflow_id"""
        query = select(Node).where(Node.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workflow_id(
        self,
        session: Session,
        workflow_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count nodes by workflow_id"""
        query = select(func.count(Node.id)).where(Node.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_script_id(
        self,
        session: Session,
        *,
        script_id: str,
        include_deleted: bool = False
    ) -> List[Node]:
        """Get nodes using a specific global script"""
        query = select(Node).where(Node.script_id == script_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_custom_script_id(
        self,
        session: Session,
        *,
        custom_script_id: str,
        include_deleted: bool = False
    ) -> List[Node]:
        """Get nodes using a specific custom script"""
        query = select(Node).where(Node.custom_script_id == custom_script_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _delete_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str
    ) -> int:
        """Delete all nodes by workflow_id"""
        nodes = self._get_all_by_workflow_id(session, workflow_id=workflow_id)
        count = len(nodes)
        for node in nodes:
            self._delete(session, record_id=node.id)
        return count