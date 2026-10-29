from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    created_by: Optional[str] = Field(default=None, max_length=64)
    assigned_to: Optional[str] = Field(default=None, max_length=64)
    parent_task_id: Optional[str] = Field(default=None, max_length=36)
    project_id: Optional[str] = Field(default=None, max_length=36)
    status: str = Field(default="PENDING", max_length=50)
    priority: str = Field(default="MEDIUM", max_length=50)
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    parent_task_id: Optional[str] = None
    project_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    subtasks: List["TaskResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


TaskResponse.model_rebuild()
