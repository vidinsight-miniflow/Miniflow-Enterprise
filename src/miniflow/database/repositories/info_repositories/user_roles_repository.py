from typing import Optional, Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..base_repository import BaseRepository
from ...models.info_models.user_roles_model import UserRoles


class UserRolesRepository(BaseRepository[UserRoles]):
    def __init__(self):
        super().__init__(UserRoles)