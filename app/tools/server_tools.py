import base64
import json
import re
from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class ExecuteCommandTool(BaseTool):
    name = "server.execute_command"
    description = (
        "Execute any shell command on the VICKY server with unrestricted access. "
        "Allows running Docker, Git, systemd, inspecting files, installing packages, or diagnosing issues."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The exact shell command to execute"},
            "cwd": {"type": "string", "description": "Optional working directory"},
            "timeout": {"type": "number", "description": "Optional timeout in seconds"},
            "sudo": {"type": "boolean", "description": "Whether to execute with sudo/root privileges"},
        },
        "required": ["command"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        command = kwargs.get("command")
        if not command:
            return ToolResult(success=False, error="Missing required parameter 'command'")

        cwd = kwargs.get("cwd")
        timeout = kwargs.get("timeout")
        sudo = kwargs.get("sudo", False)

        res = provider.execute(command, cwd=cwd, timeout=timeout, sudo=sudo)
        return ToolResult(
            success=res.success,
            data={
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.exit_code,
                "timed_out": res.timed_out,
                "duration_ms": res.duration_ms,
            },
            raw_output=res.stdout if res.success else f"Error (code {res.exit_code}):\n{res.stderr}\n{res.stdout}",
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GetSystemInfoTool(BaseTool):
    name = "server.get_system_info"
    description = "Retrieve server hostname, OS distribution, kernel version, architecture, and uptime."
    parameters = {"type": "object", "properties": {}}

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cmd = (
            "echo '---HOSTNAME---' && hostname && "
            "echo '---UNAME---' && uname -a && "
            "echo '---UPTIME---' && uptime && "
            "echo '---OS---' && cat /etc/os-release | grep -E '^(NAME|VERSION)=' 2>/dev/null"
        )
        res = provider.execute(cmd)
        if not res.success:
            return ToolResult(success=False, error=res.stderr, raw_output=res.stderr)

        text = res.stdout
        info: Dict[str, Any] = {}

        if "---HOSTNAME---" in text:
            parts = text.split("---HOSTNAME---")[1].split("---UNAME---")
            info["hostname"] = parts[0].strip()

            parts2 = parts[1].split("---UPTIME---")
            info["kernel"] = parts2[0].strip()

            parts3 = parts2[1].split("---OS---")
            info["uptime"] = parts3[0].strip()

            os_lines = [l.strip() for l in parts3[1].strip().splitlines() if l.strip()]
            info["os"] = " ".join([l.replace('"', '').replace('NAME=', '').replace('VERSION=', '') for l in os_lines])

        return ToolResult(success=True, data=info, raw_output=res.stdout, duration_ms=res.duration_ms)


class GetResourcesTool(BaseTool):
    name = "server.get_resources"
    description = "Retrieve server resource usage: CPU load, RAM total/available, and root filesystem disk space."
    parameters = {"type": "object", "properties": {}}

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cmd = (
            "echo '---CPU---' && nproc && cat /proc/loadavg && "
            "echo '---RAM---' && free -m && "
            "echo '---DISK---' && df -h /"
        )
        res = provider.execute(cmd)
        if not res.success:
            return ToolResult(success=False, error=res.stderr, raw_output=res.stderr)

        return ToolResult(success=True, data={"raw": res.stdout}, raw_output=res.stdout, duration_ms=res.duration_ms)


class ListProcessesTool(BaseTool):
    name = "server.list_processes"
    description = "Inspect running system processes with optional search filter."
    parameters = {
        "type": "object",
        "properties": {
            "filter_name": {"type": "string", "description": "Optional process name keyword to filter by"},
            "limit": {"type": "integer", "description": "Maximum number of processes to return (default 25)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        filter_name = kwargs.get("filter_name")
        limit = kwargs.get("limit", 25)

        if filter_name:
            cmd = f"ps aux | grep -i '{filter_name}' | grep -v grep | head -n {limit}"
        else:
            cmd = f"ps aux --sort=-%mem | head -n {limit}"

        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class ReadFileTool(BaseTool):
    name = "server.read_file"
    description = "Read contents of a file on the server with optional line range."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to file"},
            "start_line": {"type": "integer", "description": "1-based starting line number"},
            "end_line": {"type": "integer", "description": "Ending line number"},
        },
        "required": ["path"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, error="Missing required parameter 'path'")

        start_line = kwargs.get("start_line")
        end_line = kwargs.get("end_line")

        if start_line is not None and end_line is not None:
            cmd = f"sed -n '{start_line},{end_line}p' {path}"
        elif start_line is not None:
            cmd = f"tail -n +{start_line} {path}"
        elif end_line is not None:
            cmd = f"head -n {end_line} {path}"
        else:
            cmd = f"cat {path}"

        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"content": res.stdout, "path": path},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class WriteFileTool(BaseTool):
    name = "server.write_file"
    description = "Write or overwrite content to a file on the server."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "content": {"type": "string", "description": "File contents to write"},
            "append": {"type": "boolean", "description": "If true, append to file instead of overwrite"},
        },
        "required": ["path", "content"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        content = kwargs.get("content", "")
        append = kwargs.get("append", False)

        if not path:
            return ToolResult(success=False, error="Missing parameter 'path'")

        # Safely transmit content via base64 decoding on remote host
        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        op = ">>" if append else ">"
        cmd = f"mkdir -p $(dirname '{path}') && echo '{b64}' | base64 -d {op} '{path}'"

        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"path": path, "bytes_written": len(content)},
            raw_output=f"Successfully wrote {len(content)} bytes to {path}" if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class EditFileTool(BaseTool):
    name = "server.edit_file"
    description = (
        "Perform targeted find-and-replace on a file on the server. "
        "Replaces exact occurrence of target string with replacement text."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "target": {"type": "string", "description": "Exact text substring to be replaced"},
            "replacement": {"type": "string", "description": "Replacement text"},
        },
        "required": ["path", "target", "replacement"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        path = kwargs.get("path")
        target = kwargs.get("target")
        replacement = kwargs.get("replacement")

        if not path or target is None or replacement is None:
            return ToolResult(success=False, error="Missing 'path', 'target', or 'replacement'")

        # 1. Read existing file
        read_res = provider.execute(f"cat '{path}'")
        if not read_res.success:
            return ToolResult(success=False, error=f"File not found or unreadable: {read_res.stderr}")

        content = read_res.stdout
        if target not in content:
            return ToolResult(
                success=False,
                error=f"Target string not found in {path}. Please inspect the file with server.read_file first.",
            )

        new_content = content.replace(target, replacement, 1)

        # 2. Write updated file via base64
        b64 = base64.b64encode(new_content.encode("utf-8")).decode("ascii")
        write_res = provider.execute(f"echo '{b64}' | base64 -d > '{path}'")

        return ToolResult(
            success=write_res.success,
            data={"path": path, "replaced": True},
            raw_output=f"Successfully edited {path}" if write_res.success else write_res.stderr,
            error=write_res.stderr if not write_res.success else None,
            duration_ms=write_res.duration_ms,
        )


class SearchFilesTool(BaseTool):
    name = "server.search_files"
    description = "Search for files by name glob or grep for text inside files."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory to search in (default '.')"},
            "name_pattern": {"type": "string", "description": "Filename pattern (e.g. '*.yml', 'Dockerfile')"},
            "contains_text": {"type": "string", "description": "Grep search string inside files"},
            "max_results": {"type": "integer", "description": "Max lines/matches to return (default 30)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        base_path = kwargs.get("path", ".")
        name_pattern = kwargs.get("name_pattern")
        contains_text = kwargs.get("contains_text")
        max_results = kwargs.get("max_results", 30)

        if contains_text:
            name_filter = f"-name '{name_pattern}'" if name_pattern else ""
            cmd = f"grep -rnI '{contains_text}' {base_path} 2>/dev/null | head -n {max_results}"
        elif name_pattern:
            cmd = f"find {base_path} -name '{name_pattern}' 2>/dev/null | head -n {max_results}"
        else:
            cmd = f"ls -la {base_path} | head -n {max_results}"

        res = provider.execute(cmd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
