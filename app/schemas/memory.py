from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MemoryBase(BaseModel):
    agent_id: Optional[str] = Field(default=None, max_length=64, description="Null for SHARED memory")
    type: str = Field(..., max_length=50, description="SHORT_TERM, PROJECT, LONG_TERM, SHARED")
    content: str
    importance: int = Field(default=5, ge=1, le=10)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    metadata_json: Optional[Dict[str, Any]] = None


class MemoryResponse(MemoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
