from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from ..base_repository import BaseRepository
from ...models.resource_models.variable_model import Variable


class VariableRepository(BaseRepository[Variable]):
    """Repository for Variable operations"""
    
    def __init__(self):
        super().__init__(Variable)