from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from qbitra.database.repos.base import BaseRepository, handle_exceptions
from qbitra.models.user_models.login_histor import LoginHistory
from qbitra.models.enums import LoginStatus


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    """LoginHistory repository with custom query methods."""
    
    def __init__(self):
        super().__init__(LoginHistory)