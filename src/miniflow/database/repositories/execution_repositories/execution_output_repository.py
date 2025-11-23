from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, select

from ..base_repository import BaseRepository
from ...models.execution_models.execution_output_model import ExecutionOutput


class ExecutionOutputRepository(BaseRepository[ExecutionOutput]):
    """Repository for managing execution outputs"""
    
    def __init__(self):
        super().__init__(ExecutionOutput)