from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AuditLogBase(BaseModel):
    action: str = Field(..., max_length=150)
    agent_id: Optional[str] = Field(default=None, max_length=64)
    user_id: Optional[str] = Field(default=None, max_length=64)
    task_id: Optional[str] = Field(default=None, max_length=36)
    project_id: Optional[str] = Field(default=None, max_length=36)
    reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = Field(default=None, max_length=100)
    approved_by: Optional[str] = Field(default=None, max_length=64)
    source: str = Field(default="system", max_length=100)


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
