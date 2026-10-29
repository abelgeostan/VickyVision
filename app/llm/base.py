from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_duration_ms: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    Decouples agent identities and orchestration logic from the underlying model backend.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Single prompt completion."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Multi-turn chat completion."""
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """Verify LLM service availability."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List models available on the provider."""
        pass
