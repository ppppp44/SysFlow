import platform
import subprocess
import re


# =========================================================
# Shared command helper
# =========================================================

def _run(command, timeout=3):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            encoding="utf-8",
            errors="replace",
        )

        return result.stdout.strip()

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ):
        return ""


# =========================================================
# Empty GPU result
# =========================================================

def _unavailable_gpu(name="GPU not detected"):

    return {
        "name": name,
        "available": False,
        "utilization": None,
        "temperature": None,
        "memory_used": None,
        "memory_total": None,
        "power": None,
        "clock": None,
    }


# =========================================================
# NVIDIA telemetry
# =========================================================

def _nvidia_telemetry():

    smi = _run([
        "nvidia-smi",
        "--query-gpu="
        "utilization.gpu,"
        "temperature.gpu,"
        "memory.used,"
        "memory.total,"
        "power.draw,"
        "clocks.gr",
        "--format=csv,noheader,nounits",
    ])

    if not smi:
        return None

    values = [
        value.strip()
        for value in smi.split(",")
    ]

    if len(values) < 6:
        return None

    telemetry = {
        "utilization": None,
        "temperature": None,
        "memory_used": None,
        "memory_total": None,
        "power": None,
        "clock": None,
    }

    try:
        telemetry["utilization"] = float(
            values[0]
        )
    except ValueError:
        pass

    try:
        telemetry["temperature"] = float(
            values[1]
        )
    except ValueError:
        pass

    try:
        telemetry["memory_used"] = float(
            values[2]
        )
    except ValueError:
        pass

    try:
        telemetry["memory_total"] = float(
            values[3]
        )
    except ValueError:
        pass

    try:
        telemetry["power"] = float(
            values[4]
        )
    except ValueError:
        pass

    try:
        telemetry["clock"] = float(
            values[5]
        )
    except ValueError:
        pass

    return telemetry


# =========================================================
# Linux
# =========================================================

def _linux_gpu():

    output = _run([
        "lspci"
    ])

    for line in output.splitlines():

        if not re.search(
            r"VGA compatible controller|"
            r"3D controller|"
            r"Display controller",
            line,
            re.IGNORECASE,
        ):
            continue

        name = line.split(
            ":",
            2,
        )[-1].strip()

        telemetry = {
            "utilization": None,
            "temperature": None,
            "memory_used": None,
            "memory_total": None,
            "power": None,
            "clock": None,
        }

        # -------------------------------------------------
        # NVIDIA
        # -------------------------------------------------

        if "NVIDIA" in name.upper():

            nvidia = _nvidia_telemetry()

            if nvidia is not None:
                telemetry.update(
                    nvidia
                )

        return {
            "name": name,
            "available": True,
            **telemetry,
        }

    return _unavailable_gpu()


# =========================================================
# Windows GPU name
# =========================================================

def _windows_gpu_names():

    # PowerShell is available on normal
    # Windows installations and lets us
    # query the Windows display driver.

    output = _run([
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            "Get-CimInstance "
            "Win32_VideoController | "
            "Select-Object -ExpandProperty Name"
        ),
    ])

    names = []

    for line in output.splitlines():

        name = line.strip()

        if not name:
            continue

        if name not in names:
            names.append(name)

    return names


# =========================================================
# Windows
# =========================================================

def _windows_gpu():

    names = _windows_gpu_names()

    # -----------------------------------------------------
    # NVIDIA
    # -----------------------------------------------------

    nvidia_names = [
        name
        for name in names
        if "NVIDIA" in name.upper()
    ]

    if nvidia_names:

        telemetry = (
            _nvidia_telemetry()
        )

        if telemetry is None:
            telemetry = {
                "utilization": None,
                "temperature": None,
                "memory_used": None,
                "memory_total": None,
                "power": None,
                "clock": None,
            }

        return {
            "name": nvidia_names[0],
            "available": True,
            **telemetry,
        }

    # -----------------------------------------------------
    # Other Windows GPUs
    # -----------------------------------------------------

    if names:

        return {
            "name": names[0],
            "available": True,
            "utilization": None,
            "temperature": None,
            "memory_used": None,
            "memory_total": None,
            "power": None,
            "clock": None,
        }

    return _unavailable_gpu()


# =========================================================
# macOS
# =========================================================

def _macos_gpu():

    output = _run([
        "system_profiler",
        "SPDisplaysDataType",
    ])

    if not output:
        return _unavailable_gpu(
            "GPU information unavailable"
        )

    gpu_name = None

    for line in output.splitlines():

        stripped = line.strip()

        if stripped.startswith(
            "Chipset Model:"
        ):

            gpu_name = (
                stripped.split(
                    ":",
                    1,
                )[1].strip()
            )

            break

    if gpu_name:

        return {
            "name": gpu_name,
            "available": True,
            "utilization": None,
            "temperature": None,
            "memory_used": None,
            "memory_total": None,
            "power": None,
            "clock": None,
        }

    return _unavailable_gpu()


# =========================================================
# Public API
# =========================================================

def get_gpu_info():

    system = platform.system()

    if system == "Linux":

        return _linux_gpu()

    if system == "Windows":

        return _windows_gpu()

    if system == "Darwin":

        return _macos_gpu()

    return _unavailable_gpu(
        "Unsupported platform"
    )