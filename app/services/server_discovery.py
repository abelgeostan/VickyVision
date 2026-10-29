import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.execution.base import BaseExecutionProvider
from app.execution.factory import get_execution_provider
from app.services.event_service import EventService
from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryCreate

logger = get_logger("server_discovery")


class ServerDiscoveryService:
    """Discovers and caches system infrastructure metadata for Techy and VICKY OS."""

    _cache: Optional[Dict[str, Any]] = None
    _cache_time: float = 0.0
    _cache_ttl: float = 300.0  # 5 minutes

    @classmethod
    def get_discovery(
        cls,
        provider: Optional[BaseExecutionProvider] = None,
        db: Optional[Session] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        now = time.time()
        if not force_refresh and cls._cache and (now - cls._cache_time < cls._cache_ttl):
            return cls._cache

        exec_provider = provider or get_execution_provider()
        discovery = cls._perform_discovery(exec_provider)
        cls._cache = discovery
        cls._cache_time = now

        # Optionally persist into shared memory and emit event
        if db:
            try:
                summary_text = (
                    f"Host: {discovery.get('hostname')} | OS: {discovery.get('os')} | "
                    f"Kernel: {discovery.get('kernel')} | CPU: {discovery.get('cpu_cores')} cores | "
                    f"RAM Total: {discovery.get('ram_total_mb')}MB | "
                    f"Docker: {discovery.get('docker_version')} | "
                    f"Running Containers: {len(discovery.get('running_containers', []))}"
                )
                MemoryService.create_memory(
                    db,
                    MemoryCreate(
                        agent_id="techy",
                        type="SHARED",
                        content=f"Infrastructure Discovery: {summary_text}",
                        importance=9,
                        metadata_json={"discovery": discovery},
                    ),
                )
                EventService.create_event(
                    db,
                    event_type="server.discovered",
                    source="server_discovery",
                    related_agent_id="techy",
                    payload={"hostname": discovery.get("hostname"), "os": discovery.get("os")},
                )
            except Exception as e:
                logger.warning(f"Could not persist discovery to memory/event: {e}")

        return discovery

    @classmethod
    def _perform_discovery(cls, provider: BaseExecutionProvider) -> Dict[str, Any]:
        logger.info("Executing live server discovery...", extra={"component": "discovery"})

        discovery: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "hostname": "unknown",
            "os": "unknown",
            "kernel": "unknown",
            "uptime": "unknown",
            "cpu_cores": 1,
            "ram_total_mb": 0,
            "ram_available_mb": 0,
            "disk_root_avail": "unknown",
            "ip_addresses": [],
            "docker_version": "unknown",
            "running_containers": [],
        }

        # 1. System info
        res = provider.execute("hostname && uname -r && cat /etc/os-release | grep PRETTY_NAME && uptime -p")
        if res.success:
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if len(lines) >= 1:
                discovery["hostname"] = lines[0]
            if len(lines) >= 2:
                discovery["kernel"] = lines[1]
            if len(lines) >= 3 and "PRETTY_NAME=" in lines[2]:
                discovery["os"] = lines[2].replace("PRETTY_NAME=", "").replace('"', "")
            if len(lines) >= 4:
                discovery["uptime"] = lines[3]

        # 2. CPU & RAM
        res = provider.execute("nproc && free -m | grep Mem:")
        if res.success:
            parts = res.stdout.split()
            if len(parts) >= 1 and parts[0].isdigit():
                discovery["cpu_cores"] = int(parts[0])
            if "Mem:" in res.stdout:
                mem_parts = res.stdout.split("Mem:")[1].split()
                if len(mem_parts) >= 6:
                    discovery["ram_total_mb"] = int(mem_parts[0])
                    discovery["ram_available_mb"] = int(mem_parts[5])

        # 3. Disk root
        res = provider.execute("df -h / | tail -n 1")
        if res.success:
            d_parts = res.stdout.split()
            if len(d_parts) >= 4:
                discovery["disk_root_avail"] = f"{d_parts[3]} free of {d_parts[1]} ({d_parts[4]} used)"

        # 4. IP addresses
        res = provider.execute("ip -br addr show | grep -v 'lo' | awk '{print $1 \": \" $3}'")
        if res.success:
            discovery["ip_addresses"] = [l.strip() for l in res.stdout.splitlines() if l.strip()]

        # 5. Docker
        res = provider.execute("docker --version && docker ps --format '{{.Names}} ({{.Status}})'")
        if res.success:
            d_lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if d_lines:
                discovery["docker_version"] = d_lines[0]
                discovery["running_containers"] = d_lines[1:]

        return discovery
