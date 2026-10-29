from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class ServiceStatusTool(BaseTool):
    name = "service.status"
    description = "Check the systemd status or active state of a system service."
    parameters = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Systemd service name (e.g. 'docker', 'ssh', 'nginx')"},
        },
        "required": ["service"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        service = kwargs.get("service")
        if not service:
            return ToolResult(success=False, error="Missing parameter 'service'")

        res = provider.execute(f"systemctl status {service} --no-pager -l")
        return ToolResult(
            success=res.success or res.exit_code == 3,  # Exit code 3 means inactive/stopped service
            data={"output": res.stdout},
            raw_output=res.stdout if res.stdout else res.stderr,
            error=res.stderr if res.exit_code not in (0, 3) else None,
            duration_ms=res.duration_ms,
        )


class ServiceStartTool(BaseTool):
    name = "service.start"
    description = "Start a systemd service (requires sudo if managing system services)."
    parameters = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Systemd service name"},
            "sudo": {"type": "boolean", "description": "Run with sudo (default True)"},
        },
        "required": ["service"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        service = kwargs.get("service")
        sudo = kwargs.get("sudo", True)
        res = provider.execute(f"systemctl start {service}", sudo=sudo)
        return ToolResult(
            success=res.success,
            raw_output=f"Service {service} started." if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class ServiceStopTool(BaseTool):
    name = "service.stop"
    description = "Stop a systemd service."
    parameters = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Systemd service name"},
            "sudo": {"type": "boolean", "description": "Run with sudo (default True)"},
        },
        "required": ["service"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        service = kwargs.get("service")
        sudo = kwargs.get("sudo", True)
        res = provider.execute(f"systemctl stop {service}", sudo=sudo)
        return ToolResult(
            success=res.success,
            raw_output=f"Service {service} stopped." if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class ServiceRestartTool(BaseTool):
    name = "service.restart"
    description = "Restart a systemd service."
    parameters = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Systemd service name"},
            "sudo": {"type": "boolean", "description": "Run with sudo (default True)"},
        },
        "required": ["service"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        service = kwargs.get("service")
        sudo = kwargs.get("sudo", True)
        res = provider.execute(f"systemctl restart {service}", sudo=sudo)
        return ToolResult(
            success=res.success,
            raw_output=f"Service {service} restarted." if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class ServiceLogsTool(BaseTool):
    name = "service.logs"
    description = "View recent journalctl logs for a systemd service."
    parameters = {
        "type": "object",
        "properties": {
            "service": {"type": "string", "description": "Systemd service name"},
            "lines": {"type": "integer", "description": "Number of log lines to view (default 50)"},
        },
        "required": ["service"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        service = kwargs.get("service")
        lines = kwargs.get("lines", 50)
        res = provider.execute(f"journalctl -u {service} -n {lines} --no-pager")
        return ToolResult(
            success=res.success,
            data={"logs": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
