from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DecisionRecordCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Brief summary of the decision")
    decision: str = Field(..., description="The chosen approach or decision statement")
    reason: str = Field(..., description="Rationale behind this decision")
    category: str = Field(default="ARCHITECTURE", description="Category: ARCHITECTURE, INFRASTRUCTURE, SECURITY, PROCESS")
    status: str = Field(default="PROPOSED", description="State: PROPOSED, REVIEWED, APPROVED, REJECTED, SUPERSEDED")
    proposed_by: str = Field(default="archy", description="Agent proposing the decision")
    reviewed_by: Optional[str] = Field(default=None, description="Agent reviewing (e.g. elder)")
    approved_by: Optional[str] = Field(default=None, description="Approver (e.g. human / user)")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    alternatives_considered: List[Any] = Field(default_factory=list, description="Other options considered")
    risks_identified: List[str] = Field(default_factory=list, description="Known risks or trade-offs")
    review_notes: Optional[str] = Field(default=None, description="Notes or commentary from reviewer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class DecisionRecordUpdate(BaseModel):
    status: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None
    review_notes: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class DecisionRecordResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    title: str
    category: str
    status: str
    proposed_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    decision: str
    reason: str
    alternatives_considered: List[Any] = Field(default_factory=list)
    risks_identified: List[str] = Field(default_factory=list)
    review_notes: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
