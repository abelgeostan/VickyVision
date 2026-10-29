from typing import Optional, Dict, Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    receiver_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), default="REQUEST", nullable=False, index=True)
    
    task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="SENT", nullable=False, index=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    sender = relationship("Agent", primaryjoin="foreign(Message.sender_id) == Agent.id", back_populates="sent_messages")
    receiver = relationship("Agent", primaryjoin="foreign(Message.receiver_id) == Agent.id", back_populates="received_messages")
    task = relationship("Task", back_populates="messages")
