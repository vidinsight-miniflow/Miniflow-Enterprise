from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.user_models.login_history import LoginHistory
from ...models.enums import LoginStatus


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    def __init__(self):
        super().__init__(LoginHistory)