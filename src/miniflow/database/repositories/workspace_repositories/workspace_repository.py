from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.workspace_models.workspace_model import Workspace


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self):
        super().__init__(Workspace)

    @BaseRepository._handle_db_exceptions
    def _get_by_slug(self, session: Session, slug: str, include_deleted: bool = False) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.slug == slug)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_name(self, session: Session, name: str, include_deleted: bool = False) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.name == name)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()