import re
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.llm.base import BaseLLMProvider, LLMResponse

logger = get_logger("ollama_provider")


class OllamaProvider(BaseLLMProvider):
    """
    Ollama integration conforming to BaseLLMProvider.
    Uses configurable environment settings for host and timeouts.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def _clean_response(self, text: str) -> str:
        """Removes internal thought tags from thinking models if desired, preserving actual content."""
        if not text:
            return ""
        # If response consists only of <think>...</think>, extract what's inside or clean it
        if "<think>" in text and "</think>" in text:
            parts = re.split(r"</think>", text, maxsplit=1)
            cleaned = parts[1].strip()
            if cleaned:
                return cleaned
            # If everything was inside thinking block, return the inside text stripped
            inside = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
            if inside:
                return inside.group(1).strip()
        return text.strip()

    def check_health(self) -> bool:
        """Checks if Ollama instance is reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}", extra={"component": "ollama"})
            return False

    def list_models(self) -> List[str]:
        """Returns list of model names installed on Ollama."""
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                res.raise_for_status()
                data = res.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}", extra={"component": "ollama"})
            return []

    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Calls /api/generate on Ollama."""
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if options:
            payload["options"] = options

        logger.info(f"Ollama generate request to model '{model}'", extra={"component": "ollama"})
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_text = data.get("response", "")
                content = self._clean_response(raw_text)

                return LLMResponse(
                    content=content,
                    model=model,
                    prompt_tokens=data.get("prompt_eval_count"),
                    completion_tokens=data.get("eval_count"),
                    total_duration_ms=round(data.get("total_duration", 0) / 1_000_000, 2) if data.get("total_duration") else None,
                    raw=data,
                )
        except Exception as e:
            logger.error(f"Ollama generation failed for model '{model}': {e}", extra={"component": "ollama"})
            raise RuntimeError(f"Ollama generation error: {e}") from e

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Calls /api/chat on Ollama."""
        url = f"{self.base_url}/api/chat"
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "stream": False,
        }
        if options:
            payload["options"] = options

        logger.info(f"Ollama chat request to model '{model}' ({len(messages)} messages)", extra={"component": "ollama"})
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                msg = data.get("message", {})
                raw_text = msg.get("content", "")
                content = self._clean_response(raw_text)

                return LLMResponse(
                    content=content,
                    model=model,
                    prompt_tokens=data.get("prompt_eval_count"),
                    completion_tokens=data.get("eval_count"),
                    total_duration_ms=round(data.get("total_duration", 0) / 1_000_000, 2) if data.get("total_duration") else None,
                    raw=data,
                )
        except Exception as e:
            logger.error(f"Ollama chat failed for model '{model}': {e}", extra={"component": "ollama"})
            raise RuntimeError(f"Ollama chat error: {e}") from e


def get_llm_provider() -> BaseLLMProvider:
    """Factory returns default configured LLM provider."""
    return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, timeout=settings.OLLAMA_TIMEOUT_SECONDS)
