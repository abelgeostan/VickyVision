from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AgentBase(BaseModel):
    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=100)
    description: str
    personality: str
    objectives: List[str] = Field(default_factory=list)
    system_prompt: str
    model_config_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="IDLE", max_length=50)


class AgentCreate(AgentBase):
    id: str = Field(..., max_length=64, description="Unique ID for the agent, e.g. techy, elder")


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    objectives: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    model_config_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class AgentResponse(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
