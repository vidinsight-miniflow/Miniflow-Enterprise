from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.workflow_models.edge_model import Edge


class EdgeRepository(BaseRepository[Edge]): 
    def __init__(self):
        super().__init__(Edge)