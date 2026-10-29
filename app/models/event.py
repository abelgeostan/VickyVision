from typing import Optional, Dict, Any
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    related_agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    related_task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    related_project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
