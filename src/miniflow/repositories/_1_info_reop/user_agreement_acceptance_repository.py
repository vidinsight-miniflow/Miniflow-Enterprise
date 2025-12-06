from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, func

from ..base_repository import BaseRepository
from miniflow.models import UserAgreementAcceptance


class UserAgreementAcceptanceRepository(BaseRepository[UserAgreementAcceptance]):
    def __init__(self):
        super().__init__(UserAgreementAcceptance)