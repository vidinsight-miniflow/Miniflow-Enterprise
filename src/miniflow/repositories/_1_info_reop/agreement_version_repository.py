from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from ..base_repository import BaseRepository
from miniflow.models import AgreementVersion


class AgreementVersionRepository(BaseRepository[AgreementVersion]):
    def __init__(self):
        super().__init__(AgreementVersion)

    @BaseRepository._handle_db_exceptions
    def _get_by_type_and_version(
        self, 
        session: Session, 
        *, 
        agreement_type: str, 
        version: str, 
        locale: str = "tr-TR",
        include_deleted: bool = False
    ) -> Optional[AgreementVersion]:
        query = select(AgreementVersion).where(
            and_(
                AgreementVersion.agreement_type == agreement_type,
                AgreementVersion.version == version,
                AgreementVersion.locale == locale
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_latest(
        self,
        session: Session,
        *,
        agreement_type: str,
        locale: str = "tr-TR",
        include_deleted: bool = False
    ) -> Optional[AgreementVersion]:
        """Get latest version by effective_date"""
        query = select(AgreementVersion).where(
            and_(
                AgreementVersion.agreement_type == agreement_type,
                AgreementVersion.locale == locale
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = query.order_by(desc(AgreementVersion.effective_date), desc(AgreementVersion.created_at))
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_active(
        self,
        session: Session,
        *,
        agreement_type: str,
        locale: str = "tr-TR",
        include_deleted: bool = False
    ) -> Optional[AgreementVersion]:
        """Get active version"""
        query = select(AgreementVersion).where(
            and_(
                AgreementVersion.agreement_type == agreement_type,
                AgreementVersion.locale == locale,
                AgreementVersion.is_active == True
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_type(
        self,
        session: Session,
        *,
        agreement_type: str,
        locale: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[AgreementVersion]:
        """Get all versions for a specific agreement type"""
        conditions = [AgreementVersion.agreement_type == agreement_type]
        if locale:
            conditions.append(AgreementVersion.locale == locale)
        
        query = select(AgreementVersion).where(and_(*conditions))
        query = self._apply_soft_delete_filter(query, include_deleted)
        query = query.order_by(desc(AgreementVersion.effective_date), desc(AgreementVersion.created_at))
        return list(session.execute(query).scalars().all())