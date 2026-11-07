"""Read-only local diagnostics for Monolith_v2. Python 3.11+; optional psutil."""
import json
import os
import platform
import shutil
import socket
import time
from datetime import datetime, timezone


def collect():
    """Return a bounded diagnostic snapshot; no commands executed."""
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
        "ollama": {"status": "not_checked"},
        "github": {"status": "not_checked"},
    }
    try:
        import psutil
        data["uptime_seconds"] = round(time.time() - psutil.boot_time())
        data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        data["memory"] = {"total": mem.total, "available": mem.available, "percent": mem.percent}
        disk = psutil.disk_usage("/")
        data["disk"] = {"total": disk.total, "free": disk.free, "percent": disk.percent}
    except ImportError:
        total, used, free = shutil.disk_usage("/")
        data["disk"] = {"total": total, "free": free, "percent": round(used / total * 100, 1)}
    if hasattr(os, "getloadavg"):
        data["load_average"] = list(os.getloadavg())
    return data


if __name__ == "__main__":
    print(json.dumps(collect(), ensure_ascii=False, indent=2))
