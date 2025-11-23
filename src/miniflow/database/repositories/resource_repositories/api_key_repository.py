from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from ..base_repository import BaseRepository
from ...models.resource_models.api_key_model import ApiKey


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for ApiKey operations"""
    
    def __init__(self):
        super().__init__(ApiKey)