from typing import Any, Dict, Optional
from app.execution.base import BaseExecutionProvider
from app.tools.base import BaseTool, ToolResult


class GitStatusTool(BaseTool):
    name = "git.status"
    description = "Check git status, branch name, and uncommitted or modified files in a repository directory."
    parameters = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cwd = kwargs.get("cwd", ".")
        res = provider.execute("git status", cwd=cwd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GitLogTool(BaseTool):
    name = "git.log"
    description = "Inspect recent git commit logs."
    parameters = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
            "limit": {"type": "integer", "description": "Number of commits to show (default 5)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cwd = kwargs.get("cwd", ".")
        limit = kwargs.get("limit", 5)
        res = provider.execute(f"git log -n {limit} --oneline", cwd=cwd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GitDiffTool(BaseTool):
    name = "git.diff"
    description = "Inspect git diff of unstaged or staged changes."
    parameters = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
            "file": {"type": "string", "description": "Optional specific file to diff"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cwd = kwargs.get("cwd", ".")
        file = kwargs.get("file", "")
        res = provider.execute(f"git diff {file}", cwd=cwd)
        return ToolResult(
            success=res.success,
            data={"diff": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GitBranchTool(BaseTool):
    name = "git.branch"
    description = "List local and remote git branches."
    parameters = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cwd = kwargs.get("cwd", ".")
        res = provider.execute("git branch -a", cwd=cwd)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GitPullTool(BaseTool):
    name = "git.pull"
    description = "Fetch and integrate changes from remote repository (git pull)."
    parameters = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
            "remote": {"type": "string", "description": "Remote name (default 'origin')"},
            "branch": {"type": "string", "description": "Branch name (optional)"},
        },
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        cwd = kwargs.get("cwd", ".")
        remote = kwargs.get("remote", "origin")
        branch = kwargs.get("branch", "")
        cmd = f"git pull {remote} {branch}".strip()
        res = provider.execute(cmd, cwd=cwd, timeout=60.0)
        return ToolResult(
            success=res.success,
            data={"output": res.stdout},
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )


class GitCheckoutTool(BaseTool):
    name = "git.checkout"
    description = "Switch branches or restore working tree files."
    parameters = {
        "type": "object",
        "properties": {
            "branch": {"type": "string", "description": "Branch name or commit to check out"},
            "cwd": {"type": "string", "description": "Repository directory path (default '.')"},
        },
        "required": ["branch"],
    }

    def execute(self, provider: BaseExecutionProvider, **kwargs) -> ToolResult:
        branch = kwargs.get("branch")
        cwd = kwargs.get("cwd", ".")
        res = provider.execute(f"git checkout {branch}", cwd=cwd)
        return ToolResult(
            success=res.success,
            raw_output=res.stdout if res.success else res.stderr,
            error=res.stderr if not res.success else None,
            duration_ms=res.duration_ms,
        )
