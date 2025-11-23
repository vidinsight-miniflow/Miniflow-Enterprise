from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.user_models.password_history_model import PasswordHistory


class PasswordHistoryRepository(BaseRepository[PasswordHistory]):
    def __init__(self):
        super().__init__(PasswordHistory)