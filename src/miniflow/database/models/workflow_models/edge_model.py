from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON, UniqueConstraint, CheckConstraint, Enum

from ..base_model import BaseModel
from ..enums import *


class Edge(BaseModel):
    """Workflow node bağlantıları tablosu"""
    __prefix__ = "EDG"
    __tablename__ = 'edges'
    __table_args__ = (
        CheckConstraint('from_node_id != to_node_id', name='_edge_no_self_loop'),  
        # Kaldırıldı: condition_type ile UniqueConstraint (condition_type kolonu kaldırıldı)
        UniqueConstraint('workflow_id', 'from_node_id', 'to_node_id', name='_workflow_edge_unique'),
    )

    # İlişkiler - Ana workflow ve bağlı node'lar
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workflow'da")
    from_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Başlangıç node'u")
    to_node_id = Column(String(20), ForeignKey('nodes.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hedef node'u")

    # İlişkiler
    workflow = relationship("Workflow", back_populates="edges")
    from_node = relationship("Node", foreign_keys="[Edge.from_node_id]", back_populates="outgoing_edges")
    to_node = relationship("Node", foreign_keys="[Edge.to_node_id]", back_populates="incoming_edges")

