from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Memory(Base, TimestampMixin):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # SHORT_TERM, PROJECT, LONG_TERM, SHARED
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="memories")
