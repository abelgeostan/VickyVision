from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class DecisionRecord(Base, TimestampMixin):
    """
    Persistent record of organizational, architectural, and operational decisions.
    Preserves decision provenance (proposed by, reviewed by, approved by),
    alternatives considered, reasons, and review notes.
    """
    __tablename__ = "decision_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="ARCHITECTURE", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PROPOSED", nullable=False, index=True)  # PROPOSED, REVIEWED, APPROVED, REJECTED, SUPERSEDED
    
    proposed_by: Mapped[str] = mapped_column(String(64), default="archy", nullable=False, index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives_considered: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)
    risks_identified: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    project = relationship("Project", backref="decisions")
    task = relationship("Task", backref="decisions")
