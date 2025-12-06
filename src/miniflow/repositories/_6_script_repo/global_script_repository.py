from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy import and_

from ..base_repository import BaseRepository
from miniflow.models import Script


class ScriptRepository(BaseRepository[Script]):    
    def __init__(self):
        super().__init__(Script)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Script]:
        """Get script by name"""
        query = select(Script).where(Script.name == name)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all(
        self,
        session: Session,
        include_deleted: bool = False
    ) -> List[Script]:
        """Get all scripts"""
        query = select(Script)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_category(
        self,
        session: Session,
        *,
        category: str,
        include_deleted: bool = False
    ) -> List[Script]:
        """Get scripts by category"""
        query = select(Script).where(Script.category == category)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_category_and_subcategory(
        self,
        session: Session,
        *,
        category: str,
        subcategory: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Script]:
        """Get scripts by category and subcategory"""
        conditions = [Script.category == category]
        if subcategory is not None:
            conditions.append(Script.subcategory == subcategory)
        
        query = select(Script).where(and_(*conditions))
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_all(
        self,
        session: Session,
        include_deleted: bool = False
    ) -> int:
        """Count all scripts"""
        query = select(func.count(Script.id))
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_categories(
        self,
        session: Session,
        include_deleted: bool = False
    ) -> List[str]:
        """Get distinct categories"""
        query = select(Script.category).distinct()
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = session.execute(query).scalars().all()
        return [cat for cat in result if cat is not None]
