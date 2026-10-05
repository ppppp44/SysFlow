import platform

import psutil


# =========================================================
# CPU
# =========================================================

def get_cpu_usage():
    return psutil.cpu_percent(
        interval=0.25
    )


def get_cpu_frequency():
    try:
        frequency = psutil.cpu_freq()
    except (
        AttributeError,
        OSError,
    ):
        return None

    if frequency is None:
        return None

    if frequency.current is None:
        return None

    return float(
        frequency.current
    )


def get_cpu_per_core():
    """
    Return CPU utilization for every
    logical processor.
    """

    try:
        return psutil.cpu_percent(
            interval=0.25,
            percpu=True,
        )
    except (
        AttributeError,
        OSError,
    ):
        return []


# =========================================================
# Memory
# =========================================================

def get_memory():

    try:
        memory = psutil.virtual_memory()

    except (
        AttributeError,
        OSError,
    ):
        return {
            "used": 0,
            "total": 0,
            "percent": 0.0,
        }

    return {
        "used": memory.used,
        "total": memory.total,
        "percent": memory.percent,
    }


# =========================================================
# Temperature helpers
# =========================================================

def _get_psutil_temperatures():

    try:
        return psutil.sensors_temperatures(
            fahrenheit=False
        )

    except (
        AttributeError,
        OSError,
    ):
        return {}


def _linux_cpu_temperature(
    temperatures
):
    """
    Find the best available Linux CPU
    temperature sensor.
    """

    if not temperatures:
        return None

    # -----------------------------------------------------
    # Known CPU sensor groups
    # -----------------------------------------------------

    preferred_names = [
        "coretemp",
        "k10temp",
        "zenpower",
        "cpu_thermal",
        "cpu-thermal",
        "x86_pkg_temp",
    ]

    for preferred in preferred_names:

        for sensor_name, entries in (
            temperatures.items()
        ):

            if (
                sensor_name.lower()
                != preferred.lower()
            ):
                continue

            for entry in entries:

                if entry.current is not None:

                    return float(
                        entry.current
                    )

    # -----------------------------------------------------
    # CPU-related sensor groups
    # -----------------------------------------------------

    for sensor_name, entries in (
        temperatures.items()
    ):

        name = sensor_name.lower()

        if not any(
            keyword in name
            for keyword in [
                "cpu",
                "core",
                "pkg",
                "package",
                "thermal",
            ]
        ):
            continue

        for entry in entries:

            if entry.current is not None:

                return float(
                    entry.current
                )

    # -----------------------------------------------------
    # Last resort
    # -----------------------------------------------------

    for entries in (
        temperatures.values()
    ):

        for entry in entries:

            if entry.current is not None:

                return float(
                    entry.current
                )

    return None


def _windows_cpu_temperature(
    temperatures
):
    """
    psutil normally does not expose CPU
    temperature sensors on Windows.

    If a Windows installation exposes
    compatible sensors through psutil,
    use them. Otherwise return None.

    SysFlow never guesses a temperature.
    """

    if not temperatures:
        return None

    # -----------------------------------------------------
    # Prefer obvious CPU sensor names
    # -----------------------------------------------------

    preferred_keywords = [
        "cpu",
        "core",
        "package",
        "pkg",
        "processor",
    ]

    for sensor_name, entries in (
        temperatures.items()
    ):

        name = sensor_name.lower()

        if not any(
            keyword in name
            for keyword in preferred_keywords
        ):
            continue

        for entry in entries:

            if entry.current is not None:

                return float(
                    entry.current
                )

    return None


def get_cpu_temperature():
    """
    Return the best available CPU temperature
    in Celsius.

    Linux:
        Uses hwmon / thermal sensors exposed
        through psutil.

    Windows:
        Uses psutil if compatible sensors
        are exposed.

    macOS:
        Uses psutil if compatible sensors
        are exposed.

    If no trustworthy CPU temperature is
    available, return None.
    """

    temperatures = (
        _get_psutil_temperatures()
    )

    if not temperatures:
        return None

    system = platform.system()

    if system == "Linux":

        return _linux_cpu_temperature(
            temperatures
        )

    if system == "Windows":

        return _windows_cpu_temperature(
            temperatures
        )

    if system == "Darwin":

        # macOS sensor support through psutil
        # varies considerably by hardware.
        # Only use sensors that explicitly look
        # CPU-related.
        return _windows_cpu_temperature(
            temperatures
        )

    return None


# =========================================================
# All temperature sensors
# =========================================================

def get_cpu_temperature_sensors():
    """
    Return all temperature sensors exposed
    by the operating system.

    Missing sensor information is represented
    by an empty list rather than guessed values.
    """

    sensors = []

    temperatures = (
        _get_psutil_temperatures()
    )

    if not temperatures:
        return sensors

    for sensor_name, entries in (
        temperatures.items()
    ):

        for entry in entries:

            if entry.current is None:
                continue

            sensors.append({
                "sensor": sensor_name,
                "label": (
                    entry.label
                    or sensor_name
                ),
                "temperature": float(
                    entry.current
                ),
                "high": (
                    float(entry.high)
                    if entry.high is not None
                    else None
                ),
                "critical": (
                    float(entry.critical)
                    if entry.critical is not None
                    else None
                ),
            })

    return sensors