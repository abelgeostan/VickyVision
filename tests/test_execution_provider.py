import os
import pytest
from app.execution.base import ExecutionResult, redact_secrets
from app.execution.local import LocalExecutionProvider
from app.execution.ssh import SSHExecutionProvider
from app.execution.factory import get_execution_provider


def test_redact_secrets():
    text = "Connecting with pass: vickythegoat and token: secret123"
    redacted = redact_secrets(text, ["vickythegoat", "secret123"])
    assert "vickythegoat" not in redacted
    assert "secret123" not in redacted
    assert "[REDACTED]" in redacted


def test_local_execution_echo():
    provider = LocalExecutionProvider()
    res = provider.execute("echo 'hello_vicky'")
    assert res.success is True
    assert "hello_vicky" in res.stdout
    assert res.exit_code == 0
    assert res.duration_ms > 0


def test_local_execution_exit_code():
    provider = LocalExecutionProvider()
    res = provider.execute("exit 42")
    assert res.success is False
    assert res.exit_code == 42


def test_local_execution_timeout():
    provider = LocalExecutionProvider()
    res = provider.execute("python -c \"import time; time.sleep(5)\"", timeout=0.5)
    assert res.timed_out is True
    assert res.success is False


def test_ssh_provider_live_connectivity():
    """Tests live SSH connectivity to VICKY server."""
    provider = SSHExecutionProvider()
    if not provider.is_available():
        pytest.skip("VICKY server SSH is not reachable in this environment.")

    res = provider.execute("hostname")
    assert res.success is True
    assert "vicky" in res.stdout.lower()
    assert res.exit_code == 0
