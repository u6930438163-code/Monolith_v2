"""Read-only local diagnostics for Monolith_v2. Python 3.11+; optional psutil."""
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone

SERVICE_UNITS = ("ollama", "monolith-bridge", "monolith-codex")


def _service_states():
    if not shutil.which("systemctl"):
        return {name: {"status": "not_connected", "source": "systemctl",
                       "timestamp": datetime.now(timezone.utc).isoformat(), "state": None}
                for name in SERVICE_UNITS}
    states = {}
    for name in SERVICE_UNITS:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", name + ".service"],
                capture_output=True, text=True, timeout=2, check=False)
            reported_state = result.stdout.strip()
            state = reported_state if reported_state in {
                "active", "inactive", "failed", "activating", "deactivating"
            } else None
            status = state or "no_data"
        except (OSError, subprocess.TimeoutExpired):
            state, status = None, "no_data"
        states[name] = {"status": status, "source": "systemctl",
                        "timestamp": datetime.now(timezone.utc).isoformat(), "state": state or None}
    return states


def collect():
    """Return bounded local metrics and read-only status for allowlisted services."""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "uptime_seconds": None,
        "cpu_percent": None,
        "memory": None,
        "disk": None,
        "load_average": None,
        "processes": None,
        "services": {},
    }
    try:
        import psutil
        data["uptime_seconds"] = round(time.time() - psutil.boot_time())
        data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        data["memory"] = {"total": mem.total, "available": mem.available, "percent": mem.percent}
        disk = psutil.disk_usage("/")
        data["disk"] = {"total": disk.total, "free": disk.free, "percent": disk.percent}
        processes = []
        for process in psutil.process_iter(("pid", "name", "memory_info")):
            try:
                info = process.info
                memory_info = info.get("memory_info")
                processes.append({"pid": info.get("pid"), "name": info.get("name"),
                                  "rss_bytes": memory_info.rss if memory_info else 0})
            except (psutil.Error, OSError):
                continue
        data["processes"] = {"count": len(psutil.pids()),
                             "top_by_rss": sorted(processes, key=lambda item: item["rss_bytes"], reverse=True)[:10]}
    except ImportError:
        total, used, free = shutil.disk_usage("/")
        data["disk"] = {"total": total, "free": free, "percent": round(used / total * 100, 1)}
    data["services"] = _service_states()
    if hasattr(os, "getloadavg"):
        data["load_average"] = list(os.getloadavg())
    return data


if __name__ == "__main__":
    print(json.dumps(collect(), ensure_ascii=False, indent=2))
