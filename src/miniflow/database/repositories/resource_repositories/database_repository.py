from typing import List, Union, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.resource_models.database_model import Database
from ...models.enums import DatabaseType


class DatabaseRepository(BaseRepository[Database]):
    """Repository for Database operations"""
    
    def __init__(self):
        super().__init__(Database)