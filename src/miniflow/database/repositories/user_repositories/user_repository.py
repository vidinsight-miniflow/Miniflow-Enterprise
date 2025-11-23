from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.user_models.user_model import User


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)