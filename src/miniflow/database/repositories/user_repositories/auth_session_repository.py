from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.user_models.auth_session_model import AuthSession


class AuthSessionRepository(BaseRepository[AuthSession]):
    def __init__(self):
        super().__init__(AuthSession)