"""
NOTIFICATION MODEL - Stub for relationship resolution
=====================================================

Bu model User modelindeki relationship için gerekli.
Tam implementasyon daha sonra yapılacak.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..base_model import BaseModel


class Notification(BaseModel):
    """Notification stub modeli - relationship için gerekli."""
    __prefix__ = "NTF"
    __tablename__ = 'notifications'

    # User relationship
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic fields
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

