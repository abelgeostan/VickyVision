from typing import List, Dict, Any, Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.core.database import Base
from app.models.base import TimestampMixin


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    objectives: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_config_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="IDLE", nullable=False, index=True)

    # Relationships
    created_tasks = relationship(
        "Task",
        primaryjoin="foreign(Task.created_by) == Agent.id",
        back_populates="creator",
        lazy="selectin",
    )
    assigned_tasks = relationship(
        "Task",
        primaryjoin="foreign(Task.assigned_to) == Agent.id",
        back_populates="assignee",
        lazy="selectin",
    )
    sent_messages = relationship(
        "Message",
        primaryjoin="foreign(Message.sender_id) == Agent.id",
        back_populates="sender",
        lazy="selectin",
    )
    received_messages = relationship(
        "Message",
        primaryjoin="foreign(Message.receiver_id) == Agent.id",
        back_populates="receiver",
        lazy="selectin",
    )
    memories = relationship(
        "Memory",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approval_requests = relationship(
        "ApprovalRequest",
        primaryjoin="foreign(ApprovalRequest.requesting_agent_id) == Agent.id",
        back_populates="requesting_agent",
        lazy="selectin",
    )
