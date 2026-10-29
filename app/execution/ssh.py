import time
import socket
import paramiko
from typing import Optional, Dict
from app.core.config import settings
from app.core.logging import get_logger
from app.execution.base import BaseExecutionProvider, ExecutionResult, redact_secrets

logger = get_logger("ssh_exec_provider")


class SSHExecutionProvider(BaseExecutionProvider):
    """
    Executes commands on the target Ubuntu server via persistent SSH connection.
    Used when VICKY OS backend is running in Docker or on a separate management machine.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        sudo_password: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.host = host or settings.TECHY_SSH_HOST
        self.port = port or settings.TECHY_SSH_PORT
        self.username = username or settings.TECHY_SSH_USER
        self.password = password or settings.TECHY_SSH_PASSWORD
        self.key_filename = key_filename or settings.TECHY_SSH_KEY_PATH or None
        self.sudo_password = sudo_password or settings.TECHY_SUDO_PASSWORD
        self.default_timeout = timeout or settings.TECHY_EXEC_TIMEOUT_SECONDS
        self._client: Optional[paramiko.SSHClient] = None

    def get_provider_type(self) -> str:
        return "ssh"

    def _get_client(self) -> paramiko.SSHClient:
        """Returns active SSH client or initializes a new connection."""
        if self._client is not None:
            transport = self._client.get_transport()
            if transport is not None and transport.is_active():
                return self._client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "timeout": 10.0,
        }
        if self.key_filename:
            connect_kwargs["key_filename"] = self.key_filename
        if self.password:
            connect_kwargs["password"] = self.password

        client.connect(**connect_kwargs)
        self._client = client
        logger.info(f"Connected SSH session to {self.username}@{self.host}:{self.port}", extra={"component": "ssh_exec"})
        return self._client

    def is_available(self) -> bool:
        try:
            client = self._get_client()
            transport = client.get_transport()
            return transport is not None and transport.is_active()
        except Exception as e:
            logger.warning(f"SSH availability check failed: {e}", extra={"component": "ssh_exec"})
            return False

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        sudo: bool = False,
    ) -> ExecutionResult:
        timeout_val = timeout or self.default_timeout
        start_time = time.perf_counter()

        cmd_parts = []
        if env:
            env_str = " ".join([f"{k}='{v}'" for k, v in env.items()])
            cmd_parts.append(f"export {env_str}")
        if cwd:
            cmd_parts.append(f"cd {cwd}")

        actual_cmd = command
        stdin_data = None

        if sudo:
            if self.sudo_password:
                actual_cmd = f"echo '{self.sudo_password}' | sudo -S {command}"
            else:
                actual_cmd = f"sudo {command}"

        cmd_parts.append(actual_cmd)
        full_command = " && ".join(cmd_parts) if (cwd or env) else actual_cmd

        secrets_to_redact = []
        if self.password:
            secrets_to_redact.append(self.password)
        if self.sudo_password:
            secrets_to_redact.append(self.sudo_password)

        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = 0

        try:
            client = self._get_client()
            stdin, stdout, stderr = client.exec_command(full_command, timeout=timeout_val)

            channel = stdout.channel
            channel.settimeout(timeout_val)

            # Read output
            stdout_str = stdout.read().decode("utf-8", errors="replace")
            stderr_str = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()

        except socket.timeout:
            timed_out = True
            exit_code = -1
            stderr_str += f"\nSSH execution timed out after {timeout_val} seconds."
            self.close()  # Reset client on timeout
        except Exception as e:
            exit_code = 1
            stderr_str += f"\nSSH execution exception: {str(e)}"
            self.close()

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

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
