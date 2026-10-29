from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ApprovalCreate(BaseModel):
    requesting_agent_id: str = Field(..., max_length=64)
    task_id: Optional[str] = Field(default=None, max_length=36)
    project_id: Optional[str] = Field(default=None, max_length=36)
    action: str = Field(..., max_length=255)
    reason: str
    risk_level: str = Field(default="MEDIUM", max_length=50)


class ApprovalDecision(BaseModel):
    status: str = Field(..., description="APPROVED, REJECTED, or REQUEST_CHANGES")
    approved_by: str = Field(..., max_length=64)
    rejection_reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    requesting_agent_id: str
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    action: str
    reason: str
    risk_level: str
    status: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
