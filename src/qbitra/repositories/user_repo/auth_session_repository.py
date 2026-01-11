from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from qbitra.database.repos.base import BaseRepository, handle_exceptions
from qbitra.models.user_models.auth_session import AuthSession


class AuthSessionRepository(BaseRepository[AuthSession]):
    """AuthSession repository with custom query methods."""
    
    def __init__(self):
        super().__init__(AuthSession)