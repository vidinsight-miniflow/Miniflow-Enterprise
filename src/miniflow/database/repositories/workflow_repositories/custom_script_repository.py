from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from ..base_repository import BaseRepository
from ...models.workflow_models.custom_script_model import CustomScript
from ...utils.filter_params import FilterParams


class CustomScriptRepository(BaseRepository[CustomScript]): 
    def __init__(self):
        super().__init__(CustomScript)