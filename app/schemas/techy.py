from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TechyExecuteRequest(BaseModel):
    instruction: str = Field(..., description="The objective or instruction for Techy to perform")
    task_id: Optional[str] = Field(default=None, description="Optional existing task ID; creates a new task if omitted")
    project_id: Optional[str] = Field(default=None, description="Optional project association")
    max_steps: Optional[int] = Field(default=15, description="Max tool execution iterations")
    timeout_seconds: Optional[float] = Field(default=180.0, description="Total maximum execution duration")
    verify_post_action: bool = Field(default=True, description="Verify state after significant modifications")


class TechyStepRecord(BaseModel):
    step_number: int
    thought: str
    action: str
    args: Dict[str, Any] = Field(default_factory=dict)
    tool_success: Optional[bool] = None
    tool_output: Optional[str] = None
    tool_error: Optional[str] = None
    duration_ms: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TechyExecuteResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    steps_count: int
    execution_time_ms: float
    final_answer: str
    steps: List[TechyStepRecord] = Field(default_factory=list)
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of tool to execute directly")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")


class ToolExecuteResponse(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    raw_output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ServerDiscoveryResponse(BaseModel):
    discovery: Dict[str, Any]
    cached: bool

    model_config = ConfigDict(from_attributes=True)
