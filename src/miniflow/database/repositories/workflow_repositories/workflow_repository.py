from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.workflow_models.workflow_model import Workflow
from ...models.enums import WorkflowStatus


class WorkflowRepository(BaseRepository[Workflow]):    
    def __init__(self):
        super().__init__(Workflow)