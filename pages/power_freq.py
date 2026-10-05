import platform
import subprocess
import time
from pathlib import Path

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
)


# =========================================================
# Shared helpers
# =========================================================

def read_file(path):
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return file.read().strip()

    except (
        OSError,
        UnicodeDecodeError,
    ):
        return ""


def read_int(path):
    value = read_file(path)

    try:
        return int(value)

    except ValueError:
        return None


def read_float(path):
    value = read_file(path)

    try:
        return float(value)

    except ValueError:
        return None


def run_command(command, timeout=5):
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
# Formatting
# =========================================================

def format_frequency(mhz):

    if mhz is None:
        return "Unavailable"

    try:
        mhz = float(mhz)

    except (
        TypeError,
        ValueError,
    ):
        return "Unavailable"

    if mhz >= 1000:
        return (
            f"{mhz / 1000:.2f} GHz"
        )

    return f"{mhz:.0f} MHz"


def format_watts(watts):

    if watts is None:
        return "Unavailable"

    try:
        return f"{float(watts):.2f} W"

    except (
        TypeError,
        ValueError,
    ):
        return "Unavailable"


def format_energy(microjoules):

    if microjoules is None:
        return "Unavailable"

    try:
        joules = (
            float(microjoules)
            / 1_000_000
        )

    except (
        TypeError,
        ValueError,
    ):
        return "Unavailable"

    if joules >= 1000:

        return (
            f"{joules / 1000:.2f} kJ"
        )

    return f"{joules:.1f} J"


# =========================================================
# CPU frequency
# =========================================================

def get_cpu_frequency():

    try:

        frequency = psutil.cpu_freq()

        if frequency is not None:

            return {
                "current": frequency.current,
                "min": frequency.min,
                "max": frequency.max,
            }

    except (
        AttributeError,
        OSError,
    ):
        pass

    # -----------------------------------------------------
    # Windows fallback
    # -----------------------------------------------------

    if platform.system() == "Windows":

        output = run_command([
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "Get-CimInstance "
                "Win32_Processor | "
                "Select-Object "
                "CurrentClockSpeed,MaxClockSpeed"
            ),
        ])

        current = None
        maximum = None

        for line in output.splitlines():

            line = line.strip()

            if line.startswith(
                "CurrentClockSpeed"
            ):

                try:

                    current = float(
                        line.split(
                            ":",
                            1,
                        )[1].strip()
                    )

                except (
                    IndexError,
                    ValueError,
                ):
                    pass

            elif line.startswith(
                "MaxClockSpeed"
            ):

                try:

                    maximum = float(
                        line.split(
                            ":",
                            1,
                        )[1].strip()
                    )

                except (
                    IndexError,
                    ValueError,
                ):
                    pass

        return {
            "current": current,
            "min": None,
            "max": maximum,
        }

    return {
        "current": None,
        "min": None,
        "max": None,
    }


# =========================================================
# Linux CPU governor
# =========================================================

def get_linux_cpu_governor():

    governors = []

    cpu_root = Path(
        "/sys/devices/system/cpu"
    )

    try:

        paths = sorted(
            cpu_root.glob(
                "cpu[0-9]*/cpufreq/"
                "scaling_governor"
            )
        )

    except OSError:
        return []

    for path in paths:

        governor = read_file(
            path
        )

        if governor:
            governors.append(
                governor
            )

    return sorted(
        set(governors)
    )


# =========================================================
# Linux available governors
# =========================================================

def get_linux_available_governors():

    path = (
        "/sys/devices/system/cpu/"
        "cpu0/cpufreq/"
        "scaling_available_governors"
    )

    value = read_file(
        path
    )

    if not value:
        return []

    return value.split()


# =========================================================
# Linux CPU policy
# =========================================================

def get_linux_cpu_policy():

    policies = []

    root = Path(
        "/sys/devices/system/cpu"
    )

    try:

        paths = sorted(
            root.glob(
                "cpufreq/policy*/"
                "scaling_cur_freq"
            )
        )

        if not paths:

            paths = sorted(
                root.glob(
                    "cpu*/cpufreq/"
                    "scaling_cur_freq"
                )
            )

    except OSError:
        return policies

    for path in paths:

        frequency = read_int(
            path
        )

        if frequency is None:
            continue

        # sysfs reports kHz
        policies.append(
            frequency / 1000
        )

    return policies


# =========================================================
# Windows frequency policy
# =========================================================

def get_windows_frequency_policy():

    """
    Windows does not expose Linux-style CPU
    governors such as performance/powersave
    through the same interface.

    We therefore return only information that
    can be reliably obtained.
    """

    return {
        "governors": [],
        "policies": [],
    }


# =========================================================
# Platform frequency policy
# =========================================================

def get_cpu_governor():

    if platform.system() == "Linux":

        return get_linux_cpu_governor()

    return []


def get_available_governors():

    if platform.system() == "Linux":

        return (
            get_linux_available_governors()
        )

    return []


def get_cpu_policy():

    if platform.system() == "Linux":

        return get_linux_cpu_policy()

    return []


# =========================================================
# Battery
# =========================================================

def get_battery():

    try:

        battery = (
            psutil.sensors_battery()
        )

    except (
        AttributeError,
        OSError,
    ):
        return None

    if battery is None:
        return None

    return {
        "percent": battery.percent,
        "plugged": battery.power_plugged,
        "seconds_left": battery.secsleft,
    }


def format_battery_time(seconds):

    if seconds is None:
        return "Unavailable"

    if (
        seconds
        == psutil.POWER_TIME_UNLIMITED
    ):
        return "Unlimited"

    if (
        seconds
        == psutil.POWER_TIME_UNKNOWN
    ):
        return "Unknown"

    if seconds < 0:
        return "Unknown"

    hours = int(
        seconds // 3600
    )

    minutes = int(
        (seconds % 3600) // 60
    )

    if hours:

        return (
            f"{hours}h {minutes}m"
        )

    return f"{minutes}m"


# =========================================================
# Linux RAPL
# =========================================================

def find_rapl_energy_files():

    if platform.system() != "Linux":
        return []

    root = Path(
        "/sys/class/powercap"
    )

    files = []

    try:

        if not root.exists():
            return files

        for path in root.rglob(
            "energy_uj"
        ):

            files.append(path)

    except OSError:
        return files

    return sorted(files)


class PowerMeter:
    """
    Reads Linux Intel RAPL energy counters.

    Power is calculated from the change in
    energy over time.

    On Windows and unsupported systems,
    power remains unavailable unless a
    trustworthy platform backend is added.
    """

    def __init__(self):

        self.energy_files = (
            find_rapl_energy_files()
        )

        self.last_energy = None
        self.last_time = (
            time.monotonic()
        )

    def read_energy(self):

        if not self.energy_files:
            return None

        total = 0

        found = False

        for path in self.energy_files:

            value = read_int(
                path
            )

            if value is None:
                continue

            total += value
            found = True

        if not found:
            return None

        return total

    def get_power(self):

        now = time.monotonic()

        energy = (
            self.read_energy()
        )

        if energy is None:
            return None

        if self.last_energy is None:

            self.last_energy = {
                "value": energy,
                "time": now,
            }

            return None

        previous_energy = (
            self.last_energy["value"]
        )

        previous_time = (
            self.last_energy["time"]
        )

        self.last_energy = {
            "value": energy,
            "time": now,
        }

        elapsed = (
            now - previous_time
        )

        if elapsed <= 0:
            return None

        delta = (
            energy
            - previous_energy
        )

        # RAPL counters can wrap.
        if delta < 0:
            delta = 0

        # energy_uj -> joules
        joules = (
            delta / 1_000_000
        )

        return (
            joules / elapsed
        )

    def get_energy(self):

        return self.read_energy()


# =========================================================
# Stat card
# =========================================================

class StatCard(QFrame):

    def __init__(
        self,
        title,
        value="Unavailable",
    ):
        super().__init__()

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(5)

        self.title_label = QLabel(
            title
        )

        self.title_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self.value_label = QLabel(
            value
        )

        self.value_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 21px;
                font-weight: 700;
            }
        """)

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

        self.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)

    def set_value(
        self,
        value,
    ):

        self.value_label.setText(
            str(value)
        )


# =========================================================
# Power & Frequency page
# =========================================================

class PowerFreqPage(QWidget):

    def __init__(self):
        super().__init__()

        self.power_meter = (
            PowerMeter()
        )

        self.build_ui()

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.refresh_data
        )

        self.timer.start(
            1000
        )

        self.refresh_data()

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(16)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        title = QLabel(
            "Power & Freq"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        # -------------------------------------------------
        # Platform-specific subtitle
        # -------------------------------------------------

        if platform.system() == "Linux":

            subtitle_text = (
                "CPU frequency, power, battery, "
                "and frequency policy telemetry"
            )

        elif platform.system() == "Windows":

            subtitle_text = (
                "CPU frequency, battery, and "
                "available power telemetry"
            )

        else:

            subtitle_text = (
                "CPU frequency and power telemetry"
            )

        subtitle = QLabel(
            subtitle_text
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        stats = QGridLayout()

        stats.setHorizontalSpacing(
            12
        )

        stats.setVerticalSpacing(
            12
        )

        self.frequency_card = StatCard(
            "Current CPU Frequency"
        )

        self.max_frequency_card = StatCard(
            "Maximum Frequency"
        )

        self.power_card = StatCard(
            "Estimated CPU Package Power"
        )

        self.governor_card = StatCard(
            "CPU Governor"
        )

        stats.addWidget(
            self.frequency_card,
            0,
            0,
        )

        stats.addWidget(
            self.max_frequency_card,
            0,
            1,
        )

        stats.addWidget(
            self.power_card,
            1,
            0,
        )

        stats.addWidget(
            self.governor_card,
            1,
            1,
        )

        layout.addLayout(
            stats
        )

        # -------------------------------------------------
        # Battery
        # -------------------------------------------------

        battery_frame = QFrame()

        battery_layout = QVBoxLayout(
            battery_frame
        )

        battery_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        battery_title = QLabel(
            "Battery"
        )

        battery_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        self.battery_status = QLabel(
            "Unavailable"
        )

        self.battery_status.setStyleSheet("""
            QLabel {
                color: #9da5b3;
                font-size: 14px;
            }
        """)

        battery_layout.addWidget(
            battery_title
        )

        battery_layout.addWidget(
            self.battery_status
        )

        battery_frame.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)

        layout.addWidget(
            battery_frame
        )

        # -------------------------------------------------
        # Frequency policy
        # -------------------------------------------------

        policy_frame = QFrame()

        policy_layout = QVBoxLayout(
            policy_frame
        )

        policy_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        policy_title = QLabel(
            "Frequency Policy"
        )

        policy_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        self.policy_status = QLabel(
            "Unavailable"
        )

        self.policy_status.setWordWrap(
            True
        )

        self.policy_status.setStyleSheet("""
            QLabel {
                color: #9da5b3;
                font-size: 14px;
            }
        """)

        policy_layout.addWidget(
            policy_title
        )

        policy_layout.addWidget(
            self.policy_status
        )

        policy_frame.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)

        layout.addWidget(
            policy_frame
        )

        # -------------------------------------------------
        # Energy
        # -------------------------------------------------

        energy_frame = QFrame()

        energy_layout = QVBoxLayout(
            energy_frame
        )

        energy_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        energy_title = QLabel(
            "Energy Counter"
        )

        energy_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        self.energy_status = QLabel(
            "Unavailable"
        )

        self.energy_status.setStyleSheet("""
            QLabel {
                color: #9da5b3;
                font-size: 14px;
            }
        """)

        energy_layout.addWidget(
            energy_title
        )

        energy_layout.addWidget(
            self.energy_status
        )

        energy_frame.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)

        layout.addWidget(
            energy_frame
        )

        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                background: #111318;
                color: #ffffff;
            }
        """)

    # =====================================================
    # Refresh
    # =====================================================

    def refresh_data(self):

        frequency = (
            get_cpu_frequency()
        )

        self.frequency_card.set_value(
            format_frequency(
                frequency["current"]
            )
        )

        self.max_frequency_card.set_value(
            format_frequency(
                frequency["max"]
            )
        )

        # -------------------------------------------------
        # Power
        # -------------------------------------------------

        power = (
            self.power_meter.get_power()
        )

        self.power_card.set_value(
            format_watts(power)
        )

        # -------------------------------------------------
        # Governor
        # -------------------------------------------------

        governors = (
            get_cpu_governor()
        )

        if governors:

            self.governor_card.set_value(
                ", ".join(
                    governors
                )
            )

        elif platform.system() == "Windows":

            self.governor_card.set_value(
                "Windows-managed"
            )

        else:

            self.governor_card.set_value(
                "Unavailable"
            )

        # -------------------------------------------------
        # Battery
        # -------------------------------------------------

        battery = get_battery()

        if battery is None:

            self.battery_status.setText(
                "No battery telemetry available."
            )

        else:

            if battery["plugged"]:

                state = (
                    "Plugged in"
                )

            else:

                state = (
                    "On battery"
                )

            self.battery_status.setText(
                f"{state} • "
                f"{battery['percent']:.0f}% • "
                f"{format_battery_time(battery['seconds_left'])}"
            )

        # -------------------------------------------------
        # Frequency policy
        # -------------------------------------------------

        available = (
            get_available_governors()
        )

        policies = (
            get_cpu_policy()
        )

        if platform.system() == "Windows":

            policy_text = (
                "Windows manages CPU frequency "
                "through its power and processor "
                "performance policies."
            )

            policy_text += (
                "\nDetailed governor telemetry "
                "is unavailable."
            )

        else:

            if policies:

                policy_text = (
                    "Current policy frequencies: "
                    + ", ".join(
                        format_frequency(
                            value
                        )
                        for value in policies
                    )
                )

            else:

                policy_text = (
                    "Current frequency policy "
                    "is unavailable."
                )

            if available:

                policy_text += (
                    "\nAvailable governors: "
                    + ", ".join(
                        available
                    )
                )

        self.policy_status.setText(
            policy_text
        )

        # -------------------------------------------------
        # Energy
        # -------------------------------------------------

        energy = (
            self.power_meter.get_energy()
        )

        self.energy_status.setText(
            f"Energy counter: "
            f"{format_energy(energy)}"
        )

    # =====================================================
    # Cleanup
    # =====================================================

    def closeEvent(
        self,
        event,
    ):

        self.timer.stop()

        super().closeEvent(
            event
        )