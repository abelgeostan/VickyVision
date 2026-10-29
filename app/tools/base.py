from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.execution.base import BaseExecutionProvider


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    raw_output: Optional[str] = None
    duration_ms: float = 0.0


class BaseTool(ABC):
    """Abstract base class for all Techy tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        """Executes the tool on the target execution provider."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Returns JSON schema representation for LLM and OpenAPI."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
