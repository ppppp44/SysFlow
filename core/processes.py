import psutil
import time


def get_processes():
    """
    Return information about currently running processes.

    Linux-first implementation using psutil.
    """

    processes = []

    for proc in psutil.process_iter(
        [
            "pid",
            "name",
            "username",
            "status",
            "cpu_percent",
            "memory_percent",
            "memory_info",
            "num_threads",
            "cmdline",
            "create_time",
            "exe",
            "ppid",
        ]
    ):
        try:
            info = proc.info

            memory_info = info.get("memory_info")

            processes.append({
                "pid": info.get("pid"),
                "name": info.get("name") or "Unknown",
                "user": info.get("username") or "Unknown",
                "status": info.get("status") or "Unknown",

                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_percent": info.get("memory_percent") or 0.0,

                "memory_bytes": (
                    memory_info.rss
                    if memory_info is not None
                    else 0
                ),

                "threads": info.get("num_threads") or 0,

                "command": " ".join(info.get("cmdline") or []),

                "start_time": info.get("create_time"),

                "executable": info.get("exe") or "",

                "ppid": info.get("ppid"),
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            # Processes can disappear while we're reading them.
            # That's normal for a system monitor.
            continue

    return processes


def get_process(pid):
    """
    Get detailed information for one process.
    """

    try:
        proc = psutil.Process(pid)

        with proc.oneshot():
            memory_info = proc.memory_info()

            return {
                "pid": proc.pid,
                "name": proc.name(),
                "user": proc.username(),
                "status": proc.status(),

                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_percent": proc.memory_percent(),

                "memory_bytes": memory_info.rss,

                "threads": proc.num_threads(),

                "command": " ".join(proc.cmdline()),

                "start_time": proc.create_time(),

                "executable": proc.exe(),

                "ppid": proc.ppid(),
            }

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return None


def terminate_process(pid):
    """
    Ask a process to terminate normally.
    """

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return True

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return False


def kill_process(pid):
    """
    Forcefully kill a process.

    This should eventually require confirmation in the UI.
    """

    try:
        proc = psutil.Process(pid)
        proc.kill()
        return True

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return False


def suspend_process(pid):
    """
    Suspend a process.
    """

    try:
        proc = psutil.Process(pid)
        proc.suspend()
        return True

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return False


def resume_process(pid):
    """
    Resume a suspended process.
    """

    try:
        proc = psutil.Process(pid)
        proc.resume()
        return True

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return False


def format_bytes(value):
    """
    Convert bytes into a readable size.
    """

    if value is None:
        return "Unavailable"

    value = float(value)

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]

    for unit in units:
        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


def format_uptime(start_time):
    """
    Convert a process start timestamp into a readable age.
    """

    if not start_time:
        return "Unavailable"

    try:
        seconds = max(0, time.time() - start_time)

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}h"

        if hours > 0:
            return f"{hours}h {minutes}m"

        return f"{minutes}m"

    except (TypeError, ValueError):
        return "Unavailable"