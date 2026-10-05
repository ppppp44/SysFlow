import platform
import subprocess

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)


# =========================================================
# Shared command helper
# =========================================================

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

        return result

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ):
        return None


# =========================================================
# Linux / systemd
# =========================================================

def run_systemctl(args):
    result = run_command(
        ["systemctl", *args],
        timeout=5,
    )

    if result is None:
        return ""

    return result.stdout.strip()


def get_linux_services():
    """
    Get services managed by systemd.
    """

    output = run_systemctl([
        "list-units",
        "--type=service",
        "--all",
        "--no-legend",
        "--no-pager",
    ])

    services = []

    if not output:
        return services

    for line in output.splitlines():

        parts = line.split(None, 4)

        if len(parts) < 4:
            continue

        unit = parts[0]
        load = parts[1]
        active = parts[2]
        sub = parts[3]

        description = (
            parts[4]
            if len(parts) >= 5
            else ""
        )

        services.append({
            "name": unit,
            "load": load,
            "active": active,
            "status": sub,
            "description": description,
        })

    services.sort(
        key=lambda service:
        service["name"].lower()
    )

    return services


def control_linux_service(service, action):
    result = run_command(
        [
            "systemctl",
            action,
            service,
        ],
        timeout=10,
    )

    if result is None:
        return False

    return result.returncode == 0


# =========================================================
# Windows / Service Control Manager
# =========================================================

def get_windows_services():
    """
    Get Windows services through the built-in
    Service Control Manager command-line tool.
    """

    result = run_command(
        [
            "sc.exe",
            "query",
            "state=",
            "all",
        ],
        timeout=10,
    )

    services = []

    if result is None:
        return services

    output = result.stdout

    if not output:
        return services

    current = None

    for raw_line in output.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        # -------------------------------------------------
        # SERVICE_NAME
        # -------------------------------------------------

        if line.startswith(
            "SERVICE_NAME:"
        ):

            if current is not None:
                services.append(current)

            name = line.split(
                ":",
                1,
            )[1].strip()

            current = {
                "name": name,
                "load": "Loaded",
                "active": "Unknown",
                "status": "Unknown",
                "description": "",
            }

            continue

        if current is None:
            continue

        # -------------------------------------------------
        # DISPLAY_NAME
        # -------------------------------------------------

        if line.startswith(
            "DISPLAY_NAME:"
        ):

            display_name = line.split(
                ":",
                1,
            )[1].strip()

            current["description"] = (
                display_name
            )

            continue

        # -------------------------------------------------
        # STATE
        # -------------------------------------------------

        if line.startswith(
            "STATE"
        ):

            parts = line.split()

            if len(parts) >= 4:

                state_number = parts[1]
                state_name = parts[3]

                current["status"] = (
                    state_name
                )

                if state_name.upper() == "RUNNING":

                    current["active"] = (
                        "Active"
                    )

                elif state_name.upper() == "STOPPED":

                    current["active"] = (
                        "Inactive"
                    )

                else:

                    current["active"] = (
                        state_name.title()
                    )

            continue

    if current is not None:
        services.append(current)

    services.sort(
        key=lambda service:
        service["name"].lower()
    )

    return services


def control_windows_service(
    service,
    action,
):
    """
    Control a Windows service using sc.exe.

    Supported actions:
        start
        stop
        restart
    """

    if action == "start":

        result = run_command(
            [
                "sc.exe",
                "start",
                service,
            ],
            timeout=10,
        )

        if result is None:
            return False

        return result.returncode == 0

    if action == "stop":

        result = run_command(
            [
                "sc.exe",
                "stop",
                service,
            ],
            timeout=10,
        )

        if result is None:
            return False

        return result.returncode == 0

    if action == "restart":

        stop_result = run_command(
            [
                "sc.exe",
                "stop",
                service,
            ],
            timeout=10,
        )

        if stop_result is None:
            return False

        # If the service is already stopped,
        # sc.exe may return an error. We still
        # attempt the start operation.
        start_result = run_command(
            [
                "sc.exe",
                "start",
                service,
            ],
            timeout=10,
        )

        if start_result is None:
            return False

        return start_result.returncode == 0

    return False


# =========================================================
# Platform dispatcher
# =========================================================

def get_services():

    system = platform.system()

    if system == "Linux":

        return get_linux_services()

    if system == "Windows":

        return get_windows_services()

    return []


def control_service(
    service,
    action,
):

    system = platform.system()

    if system == "Linux":

        return control_linux_service(
            service,
            action,
        )

    if system == "Windows":

        return control_windows_service(
            service,
            action,
        )

    return False


# =========================================================
# UI
# =========================================================

class ServicesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.services = []

        self.build_ui()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.refresh_services
        )

        self.timer.start(3000)

        self.refresh_services()

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(16)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Services"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel(
            "0 services"
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

        # -------------------------------------------------
        # Description
        # -------------------------------------------------

        system = platform.system()

        if system == "Linux":

            description_text = (
                "Systemd services currently "
                "installed and loaded on Linux."
            )

        elif system == "Windows":

            description_text = (
                "Windows services managed by "
                "the Service Control Manager."
            )

        else:

            description_text = (
                "Services available on this "
                "operating system."
            )

        description = QLabel(
            description_text
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

        # -------------------------------------------------
        # Controls
        # -------------------------------------------------

        controls = QHBoxLayout()

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search services..."
        )

        self.search.textChanged.connect(
            self.refresh_table
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_services
        )

        self.start_button = QPushButton(
            "Start"
        )

        self.start_button.clicked.connect(
            lambda:
            self.perform_action(
                "start"
            )
        )

        self.stop_button = QPushButton(
            "Stop"
        )

        self.stop_button.clicked.connect(
            lambda:
            self.perform_action(
                "stop"
            )
        )

        self.restart_button = QPushButton(
            "Restart"
        )

        self.restart_button.clicked.connect(
            lambda:
            self.perform_action(
                "restart"
            )
        )

        controls.addWidget(
            self.search
        )

        controls.addWidget(
            self.refresh_button
        )

        controls.addWidget(
            self.start_button
        )

        controls.addWidget(
            self.stop_button
        )

        controls.addWidget(
            self.restart_button
        )

        layout.addLayout(
            controls
        )

        # -------------------------------------------------
        # Table
        # -------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "Service",
            "Load",
            "Active",
            "Status",
            "Description",
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
            False
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
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )

        layout.addWidget(
            self.table
        )

        # -------------------------------------------------
        # Styling
        # -------------------------------------------------

        self.setStyleSheet("""
            QWidget {
                background: #111318;
                color: #ffffff;
            }

            QLineEdit {
                background: #1a1d23;
                border: 1px solid #2b3038;
                border-radius: 8px;
                padding: 9px 12px;
                color: #ffffff;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #5b8cff;
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

            QPushButton:pressed {
                background: #252a32;
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

            QScrollBar::handle:vertical:hover {
                background: #3a414c;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    # =====================================================
    # Refresh
    # =====================================================

    def refresh_services(self):

        self.services = get_services()

        self.refresh_table()

    def refresh_table(self):

        search_text = (
            self.search.text()
            .strip()
            .lower()
        )

        filtered = []

        for service in self.services:

            if search_text:

                searchable = (
                    service["name"]
                    + " "
                    + service["description"]
                ).lower()

                if search_text not in searchable:
                    continue

            filtered.append(
                service
            )

        self.table.setRowCount(
            len(filtered)
        )

        for row, service in enumerate(
            filtered
        ):

            values = [
                service["name"],
                service["load"],
                service["active"],
                service["status"],
                service["description"],
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                if column in (
                    1,
                    2,
                    3,
                ):

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.count_label.setText(
            f"{len(filtered)} of "
            f"{len(self.services)} services"
        )

    # =====================================================
    # Selection
    # =====================================================

    def get_selected_service(self):

        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        return item.text()

    # =====================================================
    # Service control
    # =====================================================

    def perform_action(
        self,
        action,
    ):

        service = (
            self.get_selected_service()
        )

        if not service:

            QMessageBox.information(
                self,
                "No Service Selected",
                "Select a service first.",
            )

            return

        answer = QMessageBox.question(
            self,
            f"{action.title()} Service",
            (
                f"Are you sure you want to "
                f"{action} {service}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        if control_service(
            service,
            action,
        ):

            self.refresh_services()

        else:

            system = platform.system()

            if system == "Windows":

                privilege_message = (
                    "The operation may require "
                    "administrator privileges."
                )

            else:

                privilege_message = (
                    "The operation may require "
                    "root privileges."
                )

            QMessageBox.warning(
                self,
                "Service Action Failed",
                (
                    f"SysFlow could not "
                    f"{action} {service}.\n\n"
                    f"{privilege_message}"
                ),
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