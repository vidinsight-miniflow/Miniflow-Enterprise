from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..base_repository import BaseRepository
from ...models.workspace_models.workspace_invitation_model import WorkspaceInvitation
from ...models.enums import InvitationStatus


class WorkspaceInvitationRepository(BaseRepository[WorkspaceInvitation]):
    def __init__(self):
        super().__init__(WorkspaceInvitation)