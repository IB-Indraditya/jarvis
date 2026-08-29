"""
modules/system_monitor.py
=======================================================
System Monitoring
=======================================================
- CPU usage
- RAM usage
- Disk usage
- Network status
- Battery
- Running processes
- Temperature (where hardware exposes it)
"""

import psutil
from utils.helpers import bytes_to_human


def get_cpu():
    return {
        "percent": psutil.cpu_percent(interval=0.3),
        "per_core": psutil.cpu_percent(interval=0.1, percpu=True),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "freq_mhz": getattr(psutil.cpu_freq(), "current", None),
    }


def get_memory():
    vm = psutil.virtual_memory()
    return {
        "total": bytes_to_human(vm.total),
        "used": bytes_to_human(vm.used),
        "available": bytes_to_human(vm.available),
        "percent": vm.percent,
    }


def get_disk():
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "total": bytes_to_human(usage.total),
                "used": bytes_to_human(usage.used),
                "free": bytes_to_human(usage.free),
                "percent": usage.percent,
            })
        except PermissionError:
            continue
    return disks


def get_network():
    io = psutil.net_io_counters()
    return {
        "bytes_sent": bytes_to_human(io.bytes_sent),
        "bytes_recv": bytes_to_human(io.bytes_recv),
        "connections": len(psutil.net_connections()) if hasattr(psutil, "net_connections") else None,
    }


def get_battery():
    batt = psutil.sensors_battery()
    if not batt:
        return None
    return {
        "percent": batt.percent,
        "plugged_in": batt.power_plugged,
        "secs_left": batt.secsleft if batt.secsleft not in (-1, -2) else None,
    }


def get_temperatures():
    try:
        temps = psutil.sensors_temperatures()
        return {
            name: [{"label": e.label or name, "current": e.current} for e in entries]
            for name, entries in temps.items()
        }
    except (AttributeError, NotImplementedError):
        return {}


def get_processes(limit: int = 15):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    return procs[:limit]


def full_snapshot():
    """Everything the dashboard's system-monitor widgets need in one call."""
    return {
        "cpu": get_cpu(),
        "memory": get_memory(),
        "disk": get_disk(),
        "network": get_network(),
        "battery": get_battery(),
        "temperatures": get_temperatures(),
        "top_processes": get_processes(),
    }
