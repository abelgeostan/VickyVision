from typing import List, Dict, Any, Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PLANNING", nullable=False, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    objectives: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
