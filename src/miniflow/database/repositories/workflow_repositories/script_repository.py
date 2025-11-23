from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from ..base_repository import BaseRepository
from ...models.workflow_models.script_model import Script
from ...utils.filter_params import FilterParams


class ScriptRepository(BaseRepository[Script]):    
    def __init__(self):
        super().__init__(Script)
