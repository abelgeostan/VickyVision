import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    timed_out: bool = False
    cwd: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def redact_secrets(text: str, secrets: Optional[List[str]] = None) -> str:
    """Redacts known passwords and sensitive credentials from log and output strings."""
    if not text or not secrets:
        return text or ""
    redacted = text
    for secret in secrets:
        if secret and len(secret) > 2:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


class BaseExecutionProvider(ABC):
    """
    Abstract interface for executing system and shell commands on the target host.
    Decouples Techy tools from physical execution mechanics (SSH vs local subprocess).
    """

    @abstractmethod
    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        sudo: bool = False,
    ) -> ExecutionResult:
        """Executes a command on the target host."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifies if the execution provider can establish communication."""
        pass

    @abstractmethod
    def get_provider_type(self) -> str:
        """Returns provider identifier: 'ssh' or 'local'."""
        pass
