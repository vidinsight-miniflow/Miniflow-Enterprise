from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..base_repository import BaseRepository
from ...models.notification_models.notification_model import Notification
from ...models.enums import NotificationStatus, NotificationType


class NotificationRepository(BaseRepository[Notification]):
    """Repository for managing notifications"""
    
    def __init__(self):
        super().__init__(Notification)