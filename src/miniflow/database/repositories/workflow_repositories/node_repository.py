from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.workflow_models.node_model import Node


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
        *,
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Node]:
        """Get all nodes by workflow_id"""
        query = select(Node).where(Node.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalars().all()