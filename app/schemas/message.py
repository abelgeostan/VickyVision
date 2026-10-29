from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MessageBase(BaseModel):
    sender_id: str = Field(..., max_length=64)
    receiver_id: str = Field(..., max_length=64)
    content: str
    message_type: str = Field(default="REQUEST", max_length=50)
    task_id: Optional[str] = Field(default=None, max_length=36)
    project_id: Optional[str] = Field(default=None, max_length=36)
    status: str = Field(default="SENT", max_length=50)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
