from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import File


class FileRepository(BaseRepository[File]):
    """Repository for File operations"""
    
    def __init__(self):
        super().__init__(File)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[File]:
        query = select(File).where(
            and_(
                File.workspace_id == workspace_id,
                File.name == name
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[File]:
        """Get all files by workspace_id"""
        query = select(File).where(File.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count files by workspace_id"""
        query = select(func.count(File.id)).where(File.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_total_size_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Get total file size in bytes by workspace_id"""
        query = select(func.sum(File.file_size)).where(File.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_extension(
        self,
        session: Session,
        *,
        workspace_id: str,
        extension: str,
        include_deleted: bool = False
    ) -> List[File]:
        """Get files by extension"""
        query = select(File).where(
            File.workspace_id == workspace_id,
            File.file_extension == extension
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())