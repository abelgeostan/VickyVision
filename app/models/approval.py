from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    requesting_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    requesting_agent = relationship("Agent", primaryjoin="foreign(ApprovalRequest.requesting_agent_id) == Agent.id", back_populates="approval_requests")
    task = relationship("Task", back_populates="approvals")
    project = relationship("Project", backref="approval_requests")
