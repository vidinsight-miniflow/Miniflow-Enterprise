from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.workspace_models.workspace_member_model import WorkspaceMember


class WorkspaceMemberRepository(BaseRepository[WorkspaceMember]):
    def __init__(self):
        super().__init__(WorkspaceMember)