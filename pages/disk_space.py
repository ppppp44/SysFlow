import os
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
    QFrame,
    QGridLayout,
)


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
        "PB",
    ]

    for unit in units:

        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} EB"


def get_disks():
    disks = []

    seen = set()

    try:
        partitions = psutil.disk_partitions(
            all=False
        )
    except OSError:
        return disks

    for partition in partitions:

        mountpoint = partition.mountpoint

        if mountpoint in seen:
            continue

        seen.add(mountpoint)

        filesystem = partition.fstype or "Unknown"

        # Ignore pseudo filesystems that are not
        # useful as physical disk capacity.
        if filesystem.lower() in {
            "tmpfs",
            "devtmpfs",
            "devpts",
            "sysfs",
            "proc",
            "cgroup",
            "cgroup2",
            "overlay",
            "squashfs",
        }:
            continue

        try:
            usage = psutil.disk_usage(
                mountpoint
            )

        except (
            PermissionError,
            OSError,
        ):
            continue

        disks.append({
            "device": partition.device or "Unknown",
            "mountpoint": mountpoint,
            "filesystem": filesystem,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        })

    return disks


class StatCard(QFrame):

    def __init__(
        self,
        title,
        value="Unavailable",
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

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
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
            title_label
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

    def set_value(self, value):
        self.value_label.setText(
            str(value)
        )


class DiskSpacePage(QWidget):

    def __init__(self):
        super().__init__()

        self.disks = []

        self.build_ui()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.refresh_disks
        )

        self.timer.start(3000)

        self.refresh_disks()

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
            "Disk Space"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel(
            "0 filesystems"
        )

        self.count_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        header.addWidget(
            title
        )

        header.addStretch()

        header.addWidget(
            self.count_label
        )

        layout.addLayout(
            header
        )

        subtitle = QLabel(
            "Storage capacity and usage for mounted Linux filesystems."
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        layout.addWidget(
            subtitle
        )

        stats = QGridLayout()

        stats.setHorizontalSpacing(
            12
        )

        stats.setVerticalSpacing(
            12
        )

        self.total_card = StatCard(
            "Total Capacity"
        )

        self.used_card = StatCard(
            "Used Space"
        )

        self.free_card = StatCard(
            "Free Space"
        )

        self.average_card = StatCard(
            "Average Usage"
        )

        stats.addWidget(
            self.total_card,
            0,
            0,
        )

        stats.addWidget(
            self.used_card,
            0,
            1,
        )

        stats.addWidget(
            self.free_card,
            1,
            0,
        )

        stats.addWidget(
            self.average_card,
            1,
            1,
        )

        layout.addLayout(
            stats
        )

        controls = QHBoxLayout()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_disks
        )

        controls.addWidget(
            self.refresh_button
        )

        controls.addStretch()

        layout.addLayout(
            controls
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels([
            "Device",
            "Mount Point",
            "Filesystem",
            "Capacity",
            "Used",
            "Free",
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
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
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

            QScrollBar::handle:vertical:hover {
                background: #3a414c;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def refresh_disks(self):

        self.disks = get_disks()

        self.table.setRowCount(
            len(self.disks)
        )

        total_capacity = 0
        total_used = 0
        total_free = 0

        for row, disk in enumerate(
            self.disks
        ):

            total_capacity += disk["total"]
            total_used += disk["used"]
            total_free += disk["free"]

            values = [
                disk["device"],
                disk["mountpoint"],
                disk["filesystem"],
                format_bytes(
                    disk["total"]
                ),
                (
                    f"{format_bytes(disk['used'])} "
                    f"({disk['percent']:.1f}%)"
                ),
                format_bytes(
                    disk["free"]
                ),
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                if column in (
                    3,
                    4,
                    5,
                ):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item
                )

        if total_capacity > 0:

            average_usage = (
                total_used
                / total_capacity
                * 100
            )

        else:
            average_usage = None

        self.total_card.set_value(
            format_bytes(
                total_capacity
            )
            if total_capacity
            else "Unavailable"
        )

        self.used_card.set_value(
            format_bytes(
                total_used
            )
            if total_used
            else "Unavailable"
        )

        self.free_card.set_value(
            format_bytes(
                total_free
            )
            if total_free
            else "Unavailable"
        )

        self.average_card.set_value(
            (
                f"{average_usage:.1f}%"
                if average_usage is not None
                else "Unavailable"
            )
        )

        self.count_label.setText(
            f"{len(self.disks)} filesystems"
        )

    def closeEvent(self, event):

        self.timer.stop()

        super().closeEvent(event)