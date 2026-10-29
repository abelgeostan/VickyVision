from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    event_type: str = Field(..., max_length=100)
    source: str = Field(..., max_length=100)
    related_agent_id: Optional[str] = Field(default=None, max_length=64)
    related_task_id: Optional[str] = Field(default=None, max_length=36)
    related_project_id: Optional[str] = Field(default=None, max_length=36)
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
