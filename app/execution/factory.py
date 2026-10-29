from app.core.config import settings
from app.execution.base import BaseExecutionProvider
from app.execution.local import LocalExecutionProvider
from app.execution.ssh import SSHExecutionProvider

_global_provider = None


def get_execution_provider(force_type: str = None) -> BaseExecutionProvider:
    """Factory to retrieve or create the active server execution provider."""
    global _global_provider
    provider_type = (force_type or settings.TECHY_EXEC_PROVIDER).lower()

    if _global_provider is not None and _global_provider.get_provider_type() == provider_type:
        return _global_provider

    if provider_type == "local":
        _global_provider = LocalExecutionProvider()
    else:
        _global_provider = SSHExecutionProvider()

    return _global_provider
