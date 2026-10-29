from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class NetworkStatusTool(BaseTool):
    name = "network.status"
    description = "Inspect network interfaces, IP addresses, and routing table on the server."
    parameters = {"type": "object", "properties": {}}

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        res = provider.execute("ip -br addr show && echo '---ROUTES---' && ip route show")
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class NetworkConnectionsTool(BaseTool):
    name = "network.connections"
    description = "Inspect open listening TCP/UDP ports and active network sockets (ss -tulpn)."
    parameters = {
        "type": "object",
        "properties": {
            "listening_only": {"type": "boolean", "description": "Only show listening ports (default True)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        listening = kwargs.get("listening_only", True)
        flag = "-tulpn" if listening else "-tun"
        res = provider.execute(f"ss {flag}")
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
