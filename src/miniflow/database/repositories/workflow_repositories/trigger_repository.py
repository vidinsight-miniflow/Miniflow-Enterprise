from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.sql import select

from ..base_repository import BaseRepository
from ...models.workflow_models.trigger_model import Trigger


class TriggerRepository(BaseRepository[Trigger]):    
    def __init__(self):
        super().__init__(Trigger)