from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..base_repository import BaseRepository
from ...models.execution_models.execution_model import Execution
from ...models.enums import ExecutionStatus


class ExecutionRepository(BaseRepository[Execution]):
    """Repository for managing workflow executions"""
    
    def __init__(self):
        super().__init__(Execution)