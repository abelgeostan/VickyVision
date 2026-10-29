from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class DockerListContainersTool(BaseTool):
    name = "docker.list_containers"
    description = "List Docker containers on the server with their names, status, and ports."
    parameters = {
        "type": "object",
        "properties": {
            "all": {"type": "boolean", "description": "Include stopped containers if True (default True)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        show_all = kwargs.get("all", True)
        all_flag = "-a " if show_all else ""
        cmd = f"docker ps {all_flag}--format 'table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}\t{{{{.Image}}}}'"
        res = provider.execute(cmd)

        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerContainerStatusTool(BaseTool):
    name = "docker.container_status"
    description = "Inspect detailed operational status and health of a specific Docker container."
    parameters = {
        "type": "object",
        "properties": {
            "container": {"type": "string", "description": "Container name or ID"},
        },
        "required": ["container"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        container = kwargs.get("container")
        if not container:
            return ToolResult(success=False, error="Missing parameter 'container'")

        cmd = (
            f"docker inspect {container} --format "
            "'Status: {{.State.Status}} | Running: {{.State.Running}} | "
            "ExitCode: {{.State.ExitCode}} | Health: {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} | "
            "StartedAt: {{.State.StartedAt}}'"
        )
        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"status": res.stdout.strip()},
            raw_output=res.stdout.strip() if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerLogsTool(BaseTool):
    name = "docker.logs"
    description = "Retrieve recent stdout and stderr logs for a Docker container."
    parameters = {
        "type": "object",
        "properties": {
            "container": {"type": "string", "description": "Container name or ID"},
            "tail": {"type": "integer", "description": "Number of lines to show from the end (default 100)"},
        },
        "required": ["container"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        container = kwargs.get("container")
        tail = kwargs.get("tail", 100)
        if not container:
            return ToolResult(success=False, error="Missing parameter 'container'")

        cmd = f"docker logs --tail {tail} {container} 2>&1"
        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"logs": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerStartTool(BaseTool):
    name = "docker.start"
    description = "Start a stopped Docker container."
    parameters = {
        "type": "object",
        "properties": {
            "container": {"type": "string", "description": "Container name or ID to start"},
        },
        "required": ["container"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        container = kwargs.get("container")
        if not container:
            return ToolResult(success=False, error="Missing parameter 'container'")

        res = provider.execute(f"docker start {container}")
        return ToolResult(
            success=res.success,
            raw_output=f"Started container {container}" if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerStopTool(BaseTool):
    name = "docker.stop"
    description = "Stop a running Docker container."
    parameters = {
        "type": "object",
        "properties": {
            "container": {"type": "string", "description": "Container name or ID to stop"},
            "timeout": {"type": "integer", "description": "Seconds to wait before killing (default 10)"},
        },
        "required": ["container"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        container = kwargs.get("container")
        timeout = kwargs.get("timeout", 10)
        if not container:
            return ToolResult(success=False, error="Missing parameter 'container'")

        res = provider.execute(f"docker stop -t {timeout} {container}")
        return ToolResult(
            success=res.success,
            raw_output=f"Stopped container {container}" if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerRestartTool(BaseTool):
    name = "docker.restart"
    description = "Restart a Docker container."
    parameters = {
        "type": "object",
        "properties": {
            "container": {"type": "string", "description": "Container name or ID to restart"},
            "timeout": {"type": "integer", "description": "Seconds to wait before restart (default 10)"},
        },
        "required": ["container"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        container = kwargs.get("container")
        timeout = kwargs.get("timeout", 10)
        if not container:
            return ToolResult(success=False, error="Missing parameter 'container'")

        res = provider.execute(f"docker restart -t {timeout} {container}")
        return ToolResult(
            success=res.success,
            raw_output=f"Restarted container {container}" if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerBuildTool(BaseTool):
    name = "docker.build"
    description = "Build a Docker image from a Dockerfile in a specified directory."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path containing Dockerfile (default '.')"},
            "tag": {"type": "string", "description": "Optional image tag (e.g. 'my-app:latest')"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        path = kwargs.get("path", ".")
        tag = kwargs.get("tag")
        tag_flag = f"-t {tag} " if tag else ""
        res = provider.execute(f"docker build {tag_flag}{path}", timeout=300.0)

        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerComposeTool(BaseTool):
    name = "docker.compose"
    description = "Run Docker Compose commands (ps, up -d, up -d --build, down, restart, logs)."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Compose subcommand (e.g. 'ps', 'up -d --build', 'restart')"},
            "cwd": {"type": "string", "description": "Directory containing docker-compose.yml"},
            "file": {"type": "string", "description": "Optional compose filename (e.g. 'docker-compose.prod.yml')"},
        },
        "required": ["command"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        file = kwargs.get("file")

        file_flag = f"-f {file} " if file else ""
        full_cmd = f"docker compose {file_flag}{command}"

        res = provider.execute(full_cmd, cwd=cwd, timeout=300.0)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class DockerInspectTool(BaseTool):
    name = "docker.inspect"
    description = "Inspect low-level metadata of a Docker container, image, network, or volume."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Target container, image, network, or volume name/ID"},
            "format": {"type": "string", "description": "Optional Go template format string"},
        },
        "required": ["target"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        target = kwargs.get("target")
        format_tmpl = kwargs.get("format")

        fmt_flag = f"--format '{format_tmpl}' " if format_tmpl else ""
        res = provider.execute(f"docker inspect {fmt_flag}{target}")

        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
