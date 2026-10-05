import platform
import subprocess

from PySide6.QtCore import Qt
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
)


# =========================================================
# Shared command helper
# =========================================================

def run_command(command):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
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
# Linux
# =========================================================

def get_apt_apps():
    """
    Get installed Debian/Ubuntu/Mint packages.

    Uses dpkg-query to read the package database
    directly instead of scanning random files.
    """

    output = run_command([
        "dpkg-query",
        "-W",
        "-f=${binary:Package}\t"
        "${Version}\t"
        "${Architecture}\t"
        "${Status}\t"
        "${binary:Summary}\n",
    ])

    apps = []

    if not output:
        return apps

    for line in output.splitlines():

        parts = line.split(
            "\t",
            4,
        )

        if len(parts) < 5:
            continue

        name = parts[0]
        version = parts[1]
        architecture = parts[2]
        status = parts[3]
        description = parts[4]

        if (
            "install ok installed"
            not in status
        ):
            continue

        apps.append({
            "name": name,
            "version": version,
            "architecture": architecture,
            "description": description,
            "source": "APT / dpkg",
        })

    return apps


# =========================================================
# Windows
# =========================================================

def get_windows_registry_apps():

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
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "Windows Registry",
            winreg.KEY_WOW64_64KEY,
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "Windows Registry (32-bit)",
            winreg.KEY_WOW64_32KEY,
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            "Current User Registry",
            0,
        ),
    ]

    seen = set()

    for (
        hive,
        registry_path,
        source,
        view_flag,
    ) in registry_locations:

        try:

            access = (
                winreg.KEY_READ
                | view_flag
            )

            with winreg.OpenKey(
                hive,
                registry_path,
                0,
                access,
            ) as uninstall_key:

                subkey_count = (
                    winreg.QueryInfoKey(
                        uninstall_key
                    )[0]
                )

                for index in range(
                    subkey_count
                ):

                    try:

                        subkey_name = (
                            winreg.EnumKey(
                                uninstall_key,
                                index,
                            )
                        )

                    except OSError:
                        continue

                    try:

                        with winreg.OpenKey(
                            uninstall_key,
                            subkey_name,
                            0,
                            winreg.KEY_READ
                            | view_flag,
                        ) as app_key:

                            name = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "DisplayName",
                                )
                            )

                            if not name:
                                continue

                            version = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "DisplayVersion",
                                )
                                or "Unavailable"
                            )

                            publisher = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "Publisher",
                                )
                                or ""
                            )

                            architecture = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "SystemComponent",
                                )
                            )

                            # SystemComponent=1 generally means
                            # Windows treats the entry as a hidden
                            # system component rather than a normal
                            # installed application.
                            if str(
                                architecture
                            ) == "1":
                                continue

                            install_location = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "InstallLocation",
                                )
                                or ""
                            )

                            uninstall_string = (
                                _read_registry_value(
                                    winreg,
                                    app_key,
                                    "UninstallString",
                                )
                                or ""
                            )

                            description_parts = []

                            if publisher:
                                description_parts.append(
                                    publisher
                                )

                            if install_location:
                                description_parts.append(
                                    install_location
                                )

                            if uninstall_string:
                                description_parts.append(
                                    f"Uninstall: "
                                    f"{uninstall_string}"
                                )

                            description = (
                                " | ".join(
                                    description_parts
                                )
                                or "Installed application"
                            )

                            # Avoid duplicate entries
                            # between registry views.
                            identity = (
                                name.lower(),
                                str(version).lower(),
                            )

                            if identity in seen:
                                continue

                            seen.add(identity)

                            apps.append({
                                "name": str(name),
                                "version": str(
                                    version
                                ),
                                "architecture": (
                                    "32-bit"
                                    if view_flag
                                    == winreg.KEY_WOW64_32KEY
                                    else "64-bit"
                                    if view_flag
                                    == winreg.KEY_WOW64_64KEY
                                    else "User"
                                ),
                                "description": description,
                                "source": source,
                            })

                    except (
                        FileNotFoundError,
                        PermissionError,
                        OSError,
                    ):
                        continue

        except (
            FileNotFoundError,
            PermissionError,
            OSError,
        ):
            continue

    return apps


def _read_registry_value(
    winreg,
    key,
    name,
):
    try:

        value, _ = winreg.QueryValueEx(
            key,
            name,
        )

        return value

    except (
        FileNotFoundError,
        OSError,
    ):
        return None


# =========================================================
# Platform dispatcher
# =========================================================

def get_installed_apps():

    system = platform.system()

    if system == "Linux":

        apps = get_apt_apps()

    elif system == "Windows":

        apps = (
            get_windows_registry_apps()
        )

    else:

        apps = []

    apps.sort(
        key=lambda app:
        app["name"].lower()
    )

    return apps


# =========================================================
# UI
# =========================================================

class InstalledAppsPage(QWidget):

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

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Installed Apps"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel(
            "0 packages"
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

        layout.addLayout(
            header
        )

        # -------------------------------------------------
        # Description
        # -------------------------------------------------

        system = platform.system()

        if system == "Linux":

            description_text = (
                "Packages installed through "
                "the Linux package database."
            )

        elif system == "Windows":

            description_text = (
                "Applications registered in "
                "the Windows installed-app database."
            )

        else:

            description_text = (
                "Applications installed on "
                "this operating system."
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
            "Search installed apps..."
        )

        self.search.textChanged.connect(
            self.refresh_table
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_apps
        )

        controls.addWidget(
            self.search
        )

        controls.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            controls
        )

        # -------------------------------------------------
        # Table
        # -------------------------------------------------

        self.table = QTableWidget()

        self.table.setColumnCount(
            5
        )

        self.table.setHorizontalHeaderLabels([
            "Package",
            "Version",
            "Architecture",
            "Source",
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
            QHeaderView.ResizeMode.Interactive,
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

    def refresh_apps(self):

        self.apps = (
            get_installed_apps()
        )

        self.refresh_table()

    def refresh_table(self):

        search_text = (
            self.search.text()
            .strip()
            .lower()
        )

        filtered = []

        for app in self.apps:

            searchable = (
                app["name"]
                + " "
                + app["description"]
                + " "
                + app["version"]
                + " "
                + app["architecture"]
                + " "
                + app["source"]
            ).lower()

            if search_text:

                if search_text not in searchable:
                    continue

            filtered.append(
                app
            )

        self.table.setRowCount(
            len(filtered)
        )

        for row, app in enumerate(
            filtered
        ):

            values = [
                app["name"],
                app["version"],
                app["architecture"],
                app["source"],
                app["description"],
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                if column == 2:

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
            f"{len(self.apps)} packages"
        )