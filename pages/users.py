import psutil

from PySide6.QtCore import Qt, QTimer
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


def get_users():
    users = []

    try:
        sessions = psutil.users()
    except Exception:
        return users

    for session in sessions:
        users.append({
            "name": session.name or "Unknown",
            "terminal": session.terminal or "Unknown",
            "host": session.host or "Local",
            "started": session.started,
            "pid": session.pid,
        })

    return users


def format_time(timestamp):
    if not timestamp:
        return "Unknown"

    try:
        import datetime

        return datetime.datetime.fromtimestamp(
            timestamp
        ).strftime("%Y-%m-%d %H:%M")

    except (ValueError, OSError, OverflowError):
        return "Unknown"


class UsersPage(QWidget):

    def __init__(self):
        super().__init__()

        self.users = []

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.refresh_users
        )
        self.timer.start(3000)

        self.refresh_users()

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

        title = QLabel("Users")

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel(
            "0 sessions"
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
            "Users currently logged into this Linux system."
        )

        description.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        layout.addWidget(description)

        controls = QHBoxLayout()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_users
        )

        controls.addWidget(
            self.refresh_button
        )

        controls.addStretch()

        layout.addLayout(controls)

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "User",
            "Terminal",
            "Host",
            "Login Time",
            "PID",
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

        self.table.setSortingEnabled(False)

        header = self.table.horizontalHeader()

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
            QHeaderView.ResizeMode.Interactive,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Interactive,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setStretchLastSection(
            False
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

    def refresh_users(self):

        self.users = get_users()

        self.table.setRowCount(
            len(self.users)
        )

        for row, user in enumerate(
            self.users
        ):

            values = [
                user["name"],
                user["terminal"],
                user["host"],
                format_time(user["started"]),
                (
                    str(user["pid"])
                    if user["pid"]
                    else "Unknown"
                ),
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                if column == 4:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.count_label.setText(
            f"{len(self.users)} sessions"
        )

    def closeEvent(self, event):

        self.timer.stop()

        super().closeEvent(event)