import os
import subprocess
import time
from typing import Optional, Dict
from app.core.config import settings
from app.core.logging import get_logger
from app.execution.base import BaseExecutionProvider, ExecutionResult, redact_secrets

logger = get_logger("local_exec_provider")


class LocalExecutionProvider(BaseExecutionProvider):
    """
    Executes commands directly on the host using local subprocess.
    Used when VICKY OS runs natively on the target Ubuntu server.
    """

    def __init__(self, sudo_password: Optional[str] = None):
        self.sudo_password = sudo_password or settings.TECHY_SUDO_PASSWORD
        self.default_timeout = settings.TECHY_EXEC_TIMEOUT_SECONDS

    def get_provider_type(self) -> str:
        return "local"

    def is_available(self) -> bool:
        return True

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        sudo: bool = False,
    ) -> ExecutionResult:
        timeout_val = timeout or self.default_timeout
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        exec_cmd = command
        stdin_input = None

        if sudo:
            if self.sudo_password:
                exec_cmd = f"sudo -S {command}"
                stdin_input = f"{self.sudo_password}\n"
            else:
                exec_cmd = f"sudo {command}"

        start_time = time.perf_counter()
        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = 0

        secrets_to_redact = [self.sudo_password] if self.sudo_password else []

        try:
            # Use bash on Linux/macOS, cmd/powershell on Windows if local
            shell_executable = "/bin/bash" if os.name != "nt" else None
            process = subprocess.Popen(
                exec_cmd,
                shell=True,
                cwd=cwd,
                env=cmd_env,
                stdin=subprocess.PIPE if stdin_input else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable=shell_executable,
            )

            try:
                stdout_str, stderr_str = process.communicate(input=stdin_input, timeout=timeout_val)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_str, stderr_str = process.communicate()
                timed_out = True
                exit_code = -1
                stderr_str += f"\nCommand timed out after {timeout_val} seconds."

        except Exception as e:
            exit_code = 1
            stderr_str = f"Execution error: {str(e)}"

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ExecutionResult(
            command=redact_secrets(command, secrets_to_redact),
            stdout=redact_secrets(stdout_str, secrets_to_redact),
            stderr=redact_secrets(stderr_str, secrets_to_redact),
            exit_code=exit_code,
            duration_ms=duration_ms,
            timed_out=timed_out,
            cwd=cwd,
        )
