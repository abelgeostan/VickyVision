from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: str = Field(default="PLANNING", max_length=50)
    created_by: Optional[str] = Field(default=None, max_length=64)
    objectives: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[str] = None
    objectives: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
