from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.schemas.message import MessageResponse


class RouteMessageRequest(BaseModel):
    sender_id: str = Field(..., max_length=64, description="Agent ID or 'user'")
    receiver_id: str = Field(..., max_length=64, description="Agent ID to route to")
    content: str = Field(..., description="Message content")
    message_type: str = Field(default="REQUEST", max_length=50)
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    invoke_agent: bool = Field(default=True, description="Whether to invoke the receiver LLM agent and return its response")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorResponse(BaseModel):
    success: bool
    source_message: MessageResponse
    agent_response: Optional[MessageResponse] = None
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    notes: Optional[str] = None


class DispatchTaskRequest(BaseModel):
    task_id: str
    assigned_to: Optional[str] = None
    instruction: Optional[str] = None


class FlowStepRequest(BaseModel):
    flow: str = Field(..., description="Flow identifier: user_to_pa, pa_to_archy, archy_to_elder, elder_to_archy, archy_to_techy, techy_to_elder, techy_to_pa")
    content: str
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
