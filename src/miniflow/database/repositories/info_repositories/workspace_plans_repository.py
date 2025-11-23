from typing import Optional, Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..base_repository import BaseRepository
from ...models.info_models.workspace_plans_model import WorkspacePlans


class WorkspacePlansRepository(BaseRepository[WorkspacePlans]):
    def __init__(self):
        super().__init__(WorkspacePlans)