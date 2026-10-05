import os
import platform
import socket
import subprocess
import psutil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QGridLayout,
)


def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

        return result.stdout.strip()

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ):
        return ""


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read().strip()

    except (
        OSError,
        UnicodeDecodeError,
    ):
        return ""


# ---------------------------------------------------------
# Operating system
# ---------------------------------------------------------

def get_operating_system():
    system = platform.system()

    if system == "Linux":
        data = {}

        try:
            with open(
                "/etc/os-release",
                "r",
                encoding="utf-8",
            ) as file:

                for line in file:

                    if "=" not in line:
                        continue

                    key, value = line.strip().split(
                        "=",
                        1,
                    )

                    data[key] = value.strip('"')

        except OSError:
            pass

        distro = (
            data.get("PRETTY_NAME")
            or data.get("NAME")
        )

        if distro:
            return distro

        return "Linux"

    if system == "Windows":
        version = platform.release()

        if version:
            return f"Microsoft Windows {version}"

        return "Microsoft Windows"

    if system == "Darwin":
        version = platform.mac_ver()[0]

        if version:
            return f"macOS {version}"

        return "macOS"

    return system or "Unknown"


# ---------------------------------------------------------
# CPU
# ---------------------------------------------------------

def get_cpu_model():
    system = platform.system()

    if system == "Linux":

        cpu_info = read_file("/proc/cpuinfo")

        for line in cpu_info.splitlines():

            if line.lower().startswith("model name"):

                if ":" in line:
                    return line.split(
                        ":",
                        1,
                    )[1].strip()

    if system == "Windows":

        output = run_command(
            [
                "wmic",
                "cpu",
                "get",
                "name",
                "/value",
            ]
        )

        for line in output.splitlines():

            if line.lower().startswith("name="):

                name = line.split(
                    "=",
                    1,
                )[1].strip()

                if name:
                    return name

    return (
        platform.processor()
        or "Unknown"
    )


# ---------------------------------------------------------
# GPU
# ---------------------------------------------------------

def get_gpu_name():
    system = platform.system()

    if system == "Linux":

        output = run_command(["lspci"])

        for line in output.splitlines():

            if any(
                keyword in line.lower()
                for keyword in [
                    "vga compatible controller",
                    "3d controller",
                    "display controller",
                ]
            ):

                if ":" in line:
                    return line.split(
                        ":",
                        2,
                    )[-1].strip()

                return line.strip()

        return "Unknown"

    if system == "Windows":

        output = run_command(
            [
                "wmic",
                "path",
                "win32_videocontroller",
                "get",
                "name",
            ]
        )

        names = []

        for line in output.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.lower() == "name":
                continue

            names.append(line)

        if names:
            return ", ".join(names)

        return "Unknown"

    if system == "Darwin":

        output = run_command(
            [
                "system_profiler",
                "SPDisplaysDataType",
            ]
        )

        for line in output.splitlines():

            if "Chipset Model:" in line:

                return line.split(
                    ":",
                    1,
                )[1].strip()

        return "Unknown"

    return "Unknown"


# ---------------------------------------------------------
# Motherboard
# ---------------------------------------------------------

def get_motherboard():
    system = platform.system()

    if system == "Linux":

        vendor = read_file(
            "/sys/devices/virtual/dmi/id/board_vendor"
        )

        name = read_file(
            "/sys/devices/virtual/dmi/id/board_name"
        )

        if vendor and name:
            return f"{vendor} {name}"

        return (
            name
            or vendor
            or "Unknown"
        )

    if system == "Windows":

        output = run_command(
            [
                "wmic",
                "baseboard",
                "get",
                "manufacturer,product",
                "/format:list",
            ]
        )

        manufacturer = ""
        product = ""

        for line in output.splitlines():

            lower = line.lower()

            if lower.startswith("manufacturer="):
                manufacturer = line.split(
                    "=",
                    1,
                )[1].strip()

            elif lower.startswith("product="):
                product = line.split(
                    "=",
                    1,
                )[1].strip()

        if manufacturer and product:
            return f"{manufacturer} {product}"

        return (
            product
            or manufacturer
            or "Unknown"
        )

    return "Unknown"


# ---------------------------------------------------------
# BIOS
# ---------------------------------------------------------

def get_bios():
    system = platform.system()

    if system == "Linux":

        vendor = read_file(
            "/sys/devices/virtual/dmi/id/bios_vendor"
        )

        version = read_file(
            "/sys/devices/virtual/dmi/id/bios_version"
        )

        if vendor and version:
            return f"{vendor} {version}"

        return (
            version
            or vendor
            or "Unknown"
        )

    if system == "Windows":

        output = run_command(
            [
                "wmic",
                "bios",
                "get",
                "manufacturer,smbiosbiosversion",
                "/format:list",
            ]
        )

        vendor = ""
        version = ""

        for line in output.splitlines():

            lower = line.lower()

            if lower.startswith("manufacturer="):
                vendor = line.split(
                    "=",
                    1,
                )[1].strip()

            elif lower.startswith(
                "smbiosbiosversion="
            ):
                version = line.split(
                    "=",
                    1,
                )[1].strip()

        if vendor and version:
            return f"{vendor} {version}"

        return (
            version
            or vendor
            or "Unknown"
        )

    return "Unknown"


# ---------------------------------------------------------
# Formatting
# ---------------------------------------------------------

def format_bytes(value):
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


def format_uptime():
    try:
        uptime = psutil.boot_time()

        seconds = max(
            0,
            psutil.time.time() - uptime,
        )

        days = int(
            seconds // 86400
        )

        hours = int(
            (seconds % 86400) // 3600
        )

        minutes = int(
            (seconds % 3600) // 60
        )

        if days:
            return (
                f"{days}d "
                f"{hours}h "
                f"{minutes}m"
            )

        if hours:
            return (
                f"{hours}h "
                f"{minutes}m"
            )

        return f"{minutes}m"

    except (
        ValueError,
        OSError,
        TypeError,
    ):
        return "Unavailable"


def get_architecture():
    return platform.machine() or "Unknown"


def get_hostname():
    try:
        return socket.gethostname()

    except OSError:
        return "Unknown"


def get_cpu_counts():
    logical = psutil.cpu_count(
        logical=True
    )

    physical = psutil.cpu_count(
        logical=False
    )

    return physical, logical


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

class InfoCard(QFrame):

    def __init__(
        self,
        title,
        value,
    ):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(5)

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        value_label = QLabel(value)

        value_label.setWordWrap(True)

        value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        value_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 500;
            }
        """)

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        self.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)


class SystemInfoPage(QWidget):

    def __init__(self):
        super().__init__()

        self.build_ui()

    def build_ui(self):

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        outer_layout.setSpacing(16)

        title = QLabel(
            "System Info"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        subtitle = QLabel(
            "Hardware, operating system, and system information"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        outer_layout.addWidget(title)
        outer_layout.addWidget(subtitle)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        content = QWidget()

        grid = QGridLayout(
            content
        )

        grid.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        operating_system = (
            get_operating_system()
        )

        kernel = (
            platform.release()
            or "Unknown"
        )

        architecture = (
            get_architecture()
        )

        hostname = (
            get_hostname()
        )

        cpu = (
            get_cpu_model()
        )

        physical, logical = (
            get_cpu_counts()
        )

        if physical is None:
            physical_text = "Unavailable"
        else:
            physical_text = str(
                physical
            )

        if logical is None:
            logical_text = "Unavailable"
        else:
            logical_text = str(
                logical
            )

        memory = (
            psutil.virtual_memory()
        )

        memory_text = (
            f"{format_bytes(memory.total)} "
            f"({memory.percent:.1f}% currently used)"
        )

        gpu = get_gpu_name()

        motherboard = (
            get_motherboard()
        )

        bios = get_bios()

        uptime = format_uptime()

        system_info = [

            (
                "Operating System",
                operating_system,
            ),

            (
                "Kernel / Version",
                kernel,
            ),

            (
                "Architecture",
                architecture,
            ),

            (
                "Hostname",
                hostname,
            ),

            (
                "CPU",
                cpu,
            ),

            (
                "Physical Cores",
                physical_text,
            ),

            (
                "Logical Processors",
                logical_text,
            ),

            (
                "Memory",
                memory_text,
            ),

            (
                "GPU",
                gpu,
            ),

            (
                "Motherboard",
                motherboard,
            ),

            (
                "BIOS",
                bios,
            ),

            (
                "Uptime",
                uptime,
            ),
        ]

        for index, (
            name,
            value,
        ) in enumerate(system_info):

            row = index // 2
            column = index % 2

            card = InfoCard(
                name,
                value,
            )

            grid.addWidget(
                card,
                row,
                column,
            )

        grid.setColumnStretch(
            0,
            1,
        )

        grid.setColumnStretch(
            1,
            1,
        )

        scroll.setWidget(
            content
        )

        outer_layout.addWidget(
            scroll
        )

        self.setStyleSheet("""
            QWidget {
                background: #111318;
                color: #ffffff;
            }

            QScrollArea {
                background: transparent;
            }

            QScrollBar:vertical {
                background: #111318;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #2b3038;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #3a414c;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)