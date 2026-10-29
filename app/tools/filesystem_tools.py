from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class DiskUsageTool(BaseTool):
    name = "filesystem.disk_usage"
    description = "Inspect disk space usage across mounted filesystems and directory sizes."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Optional specific directory path to inspect with du -sh"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        if path:
            cmd = f"df -h {path} && echo '---DIR SIZE---' && du -sh {path} 2>/dev/null"
        else:
            cmd = "df -h -x tmpfs -x devtmpfs"

        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
