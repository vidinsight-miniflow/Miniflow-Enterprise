from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..base_repository import BaseRepository
from ...models.execution_models.execution_input_model import ExecutionInput


class ExecutionInputRepository(BaseRepository[ExecutionInput]):
    """Repository for managing execution inputs"""
    
    def __init__(self):
        super().__init__(ExecutionInput)