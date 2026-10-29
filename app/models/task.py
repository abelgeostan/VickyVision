from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    parent_task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    creator = relationship("Agent", primaryjoin="foreign(Task.created_by) == Agent.id", back_populates="created_tasks")
    assignee = relationship("Agent", primaryjoin="foreign(Task.assigned_to) == Agent.id", back_populates="assigned_tasks")
    
    # Self-referential hierarchy
    parent_task = relationship("Task", remote_side=[id], backref="subtasks")
    
    messages = relationship("Message", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
    approvals = relationship("ApprovalRequest", back_populates="task", cascade="all, delete-orphan", lazy="selectin")
