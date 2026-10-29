from typing import Any, Dict, List, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult
from app.tools.server_tools import (
    ExecuteCommandTool,
    GetSystemInfoTool,
    GetResourcesTool,
    ListProcessesTool,
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    SearchFilesTool,
)
from app.tools.docker_tools import (
    DockerListContainersTool,
    DockerContainerStatusTool,
    DockerLogsTool,
    DockerStartTool,
    DockerStopTool,
    DockerRestartTool,
    DockerBuildTool,
    DockerComposeTool,
    DockerInspectTool,
)
from app.tools.git_tools import (
    GitStatusTool,
    GitLogTool,
    GitDiffTool,
    GitBranchTool,
    GitPullTool,
    GitCheckoutTool,
)
from app.tools.service_tools import (
    ServiceStatusTool,
    ServiceStartTool,
    ServiceStopTool,
    ServiceRestartTool,
    ServiceLogsTool,
)
from app.tools.network_tools import (
    NetworkStatusTool,
    NetworkConnectionsTool,
)
from app.tools.filesystem_tools import (
    DiskUsageTool,
)
from app.core.logging import get_logger

logger = get_logger("tool_registry")


class ToolRegistry:
    """Central registry and dispatch hub for all Techy execution tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        default_tools = [
            # Server tools
            ExecuteCommandTool(),
            GetSystemInfoTool(),
            GetResourcesTool(),
            ListProcessesTool(),
            ReadFileTool(),
            WriteFileTool(),
            EditFileTool(),
            SearchFilesTool(),
            # Docker tools
            DockerListContainersTool(),
            DockerContainerStatusTool(),
            DockerLogsTool(),
            DockerStartTool(),
            DockerStopTool(),
            DockerRestartTool(),
            DockerBuildTool(),
            DockerComposeTool(),
            DockerInspectTool(),
            # Git tools
            GitStatusTool(),
            GitLogTool(),
            GitDiffTool(),
            GitBranchTool(),
            GitPullTool(),
            GitCheckoutTool(),
            # Service tools
            ServiceStatusTool(),
            ServiceStartTool(),
            ServiceStopTool(),
            ServiceRestartTool(),
            ServiceLogsTool(),
            # Network tools
            NetworkStatusTool(),
            NetworkConnectionsTool(),
            # Filesystem tools
            DiskUsageTool(),
        ]
        for tool in default_tools:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        if name in self._tools:
            return self._tools[name]
        # Fallback 1: match without category prefix (e.g. 'get_system_info' -> 'server.get_system_info')
        for full_name, tool in self._tools.items():
            if full_name.endswith(f".{name}") or full_name.lower() == name.lower():
                return tool
        return None

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def format_tools_for_prompt(self) -> str:
        """Renders tool documentation string for prompt injection."""
        docs = []
        for tool in self._tools.values():
            params = tool.parameters.get("properties", {})
            req = tool.parameters.get("required", [])
            param_desc = []
            for p_name, p_info in params.items():
                req_tag = "(required)" if p_name in req else "(optional)"
                param_desc.append(f"    - {p_name} [{p_info.get('type')}]: {p_info.get('description', '')} {req_tag}")
            
            p_str = "\n" + "\n".join(param_desc) if param_desc else "    (none)"
            docs.append(f"Tool: `{tool.name}`\n  Description: {tool.description}\n  Parameters:{p_str}")

        return "\n\n".join(docs)

    def execute(
        self,
        name: str,
        args: Dict[str, Any],
        provider: BaseExecutionProvider,
    ) -> ToolResult:
        """Validates parameters and executes the specified tool."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found. Available tools: {', '.join(self.list_tools())}",
            )

        # Basic required parameter check
        req_params = tool.parameters.get("required", [])
        for req in req_params:
            if req not in args or args[req] is None:
                return ToolResult(
                    success=False,
                    error=f"Tool '{name}' missing required argument: '{req}'",
                )

        try:
            logger.info(f"Executing tool '{name}' with args {list(args.keys())}", extra={"component": "tool_exec"})
            return tool.execute(provider, **args)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", extra={"component": "tool_exec"})
            return ToolResult(success=False, error=f"Tool execution exception: {str(e)}")


_registry_instance = None


def get_tool_registry() -> ToolRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance
