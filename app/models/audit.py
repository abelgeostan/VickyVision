from typing import Optional, Dict, Any
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    
    agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="system", nullable=False)
