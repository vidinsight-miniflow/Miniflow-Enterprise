from typing import Optional, Any, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.user_models.user_preferences_model import UserPreference


class UserPreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)