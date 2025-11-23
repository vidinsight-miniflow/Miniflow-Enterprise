from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.resource_models.file_model import File


class FileRepository(BaseRepository[File]):
    """Repository for File operations"""
    
    def __init__(self):
        super().__init__(File)