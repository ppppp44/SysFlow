import os
import platform
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


# =========================================================
# Linux
# =========================================================

LINUX_AUTOSTART_DIRS = [
    Path.home() / ".config" / "autostart",
    Path("/etc/xdg/autostart"),
]


def parse_desktop_file(path):
    data = {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if (
                    not line
                    or line.startswith("#")
                ):
                    continue

                if "=" not in line:
                    continue

                key, value = line.split(
                    "=",
                    1,
                )

                data[key] = value.strip()

    except (
        OSError,
        UnicodeDecodeError,
    ):
        return None

    return data


def get_linux_startup_apps():
    apps = []

    seen = set()

    for directory in LINUX_AUTOSTART_DIRS:

        if not directory.exists():
            continue

        try:
            files = directory.glob(
                "*.desktop"
            )

        except OSError:
            continue

        for path in files:

            path_key = str(
                path.resolve()
            )

            if path_key in seen:
                continue

            seen.add(path_key)

            data = parse_desktop_file(
                path
            )

            if not data:
                continue

            name = (
                data.get("Name")
                or path.stem
            )

            command = data.get(
                "Exec",
                "Unavailable",
            )

            hidden = (
                data.get(
                    "Hidden",
                    "false",
                ).lower()
                == "true"
            )

            disabled = (
                data.get(
                    "X-GNOME-Autostart-enabled",
                    "true",
                ).lower()
                == "false"
            )

            if hidden:

                enabled = False
                status = "Hidden"

            elif disabled:

                enabled = False
                status = "Disabled"

            else:

                enabled = True
                status = "Enabled"

            apps.append({
                "name": name,
                "command": command,
                "status": status,
                "enabled": enabled,
                "path": str(path),
            })

    return apps


# =========================================================
# Windows
# =========================================================

def get_windows_startup_apps():
    apps = []

    try:
        import winreg
    except ImportError:
        return apps

    # -----------------------------------------------------
    # Registry locations
    # -----------------------------------------------------

    registry_locations = [
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            "Current User",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
            "Current User (RunOnce)",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            "All Users",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
            "All Users (RunOnce)",
        ),
    ]

    for hive, key_path, location_name in (
        registry_locations
    ):

        try:

            with winreg.OpenKey(
                hive,
                key_path,
                0,
                winreg.KEY_READ,
            ) as key:

                index = 0

                while True:

                    try:
                        name, value, _ = (
                            winreg.EnumValue(
                                key,
                                index,
                            )
                        )

                        index += 1

                    except OSError:
                        break

                    apps.append({
                        "name": name,
                        "command": str(value),
                        "status": "Enabled",
                        "enabled": True,
                        "path": (
                            f"Registry: "
                            f"{location_name}"
                        ),
                    })

        except (
            FileNotFoundError,
            PermissionError,
            OSError,
        ):
            continue

    # -----------------------------------------------------
    # Startup folders
    # -----------------------------------------------------

    startup_folders = []

    user_startup = (
        os.environ.get(
            "APPDATA"
        )
    )

    if user_startup:

        startup_folders.append(
            Path(user_startup)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )

    program_data = (
        os.environ.get(
            "PROGRAMDATA"
        )
    )

    if program_data:

        startup_folders.append(
            Path(program_data)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "StartUp"
        )

    for directory in startup_folders:

        if not directory.exists():
            continue

        try:

            entries = list(
                directory.iterdir()
            )

        except OSError:
            continue

        for path in entries:

            if not path.is_file():
                continue

            apps.append({
                "name": path.stem,
                "command": str(path),
                "status": "Enabled",
                "enabled": True,
                "path": (
                    f"Startup folder: "
                    f"{directory}"
                ),
            })

    return apps


# =========================================================
# Platform dispatcher
# =========================================================

def get_startup_apps():

    system = platform.system()

    if system == "Linux":

        apps = get_linux_startup_apps()

    elif system == "Windows":

        apps = get_windows_startup_apps()

    else:

        apps = []

    apps.sort(
        key=lambda app: app["name"].lower()
    )

    return apps


# =========================================================
# UI
# =========================================================

class StartupPage(QWidget):

    def __init__(self):
        super().__init__()

        self.apps = []

        self.build_ui()

        self.refresh_apps()

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(16)

        header = QHBoxLayout()

        title = QLabel(
            "Startup Apps"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel(
            "0 startup apps"
        )

        self.count_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        header.addWidget(title)

        header.addStretch()

        header.addWidget(
            self.count_label
        )

        layout.addLayout(header)

        description = QLabel(
            "Applications configured to start automatically when the system logs in."
        )

        description.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        layout.addWidget(
            description
        )

        controls = QHBoxLayout()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_apps
        )

        controls.addWidget(
            self.refresh_button
        )

        controls.addStretch()

        layout.addLayout(
            controls
        )

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "Name",
            "Status",
            "Command",
            "Location",
        ])

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setSortingEnabled(
            True
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Interactive,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Interactive,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Interactive,
        )

        header.setStretchLastSection(
            True
        )

        layout.addWidget(
            self.table
        )

        self.setStyleSheet("""
            QWidget {
                background: #111318;
                color: #ffffff;
            }

            QPushButton {
                background: #1a1d23;
                border: 1px solid #2b3038;
                border-radius: 8px;
                padding: 9px 14px;
                color: #ffffff;
            }

            QPushButton:hover {
                background: #22262e;
            }

            QTableWidget {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
                gridline-color: #252a32;
                selection-background-color: #263b68;
                selection-color: #ffffff;
            }

            QHeaderView::section {
                background: #1b1f26;
                color: #9da5b3;
                border: none;
                border-bottom: 1px solid #292e37;
                padding: 9px;
                font-weight: 600;
            }

            QScrollBar:vertical {
                background: #111318;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #2b3038;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def refresh_apps(self):

        self.apps = get_startup_apps()

        self.table.setSortingEnabled(
            False
        )

        self.table.setRowCount(
            len(self.apps)
        )

        for row, app in enumerate(
            self.apps
        ):

            values = [
                app["name"],
                app["status"],
                app["command"],
                app["path"],
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                if column == 1:

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.setSortingEnabled(
            True
        )

        self.count_label.setText(
            f"{len(self.apps)} startup apps"
        )