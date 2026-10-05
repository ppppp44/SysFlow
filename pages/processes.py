from PySide6.QtCore import QTimer, Qt
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

from core.processes import (
    get_processes,
    terminate_process,
    format_bytes,
)


class ProcessesPage(QWidget):
    def __init__(self):
        super().__init__()

        self.processes = []
        self.sort_column = 2
        self.sort_reverse = True

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_processes)
        self.timer.start(2000)

        self.refresh_processes()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()

        title = QLabel("Processes")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        self.count_label = QLabel("0 processes")
        self.count_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.count_label)

        layout.addLayout(header)

        # Search + actions
        controls = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search processes...")
        self.search.textChanged.connect(self.refresh_table)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_processes)

        self.end_button = QPushButton("End Process")
        self.end_button.clicked.connect(self.end_selected_process)

        controls.addWidget(self.search)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.end_button)

        layout.addLayout(controls)

        # Process table
        self.table = QTableWidget()

        self.table.setColumnCount(8)

        self.table.setHorizontalHeaderLabels([
            "PID",
            "Name",
            "CPU",
            "Memory",
            "RAM %",
            "Threads",
            "User",
            "Status",
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

        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setStretchLastSection(True)

        self.table.setSortingEnabled(False)

        layout.addWidget(self.table)

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
        """)

    def refresh_processes(self):
        self.processes = get_processes()
        self.refresh_table()

    def refresh_table(self):
        search_text = self.search.text().strip().lower()

        filtered = []

        for process in self.processes:
            name = str(process.get("name", ""))
            pid = str(process.get("pid", ""))

            if search_text:
                if (
                    search_text not in name.lower()
                    and search_text not in pid
                ):
                    continue

            filtered.append(process)

        # Sort
        if self.sort_column == 0:
            filtered.sort(
                key=lambda p: p.get("pid") or 0,
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 1:
            filtered.sort(
                key=lambda p: str(p.get("name") or "").lower(),
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 2:
            filtered.sort(
                key=lambda p: p.get("cpu_percent") or 0,
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 3:
            filtered.sort(
                key=lambda p: p.get("memory_bytes") or 0,
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 4:
            filtered.sort(
                key=lambda p: p.get("memory_percent") or 0,
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 5:
            filtered.sort(
                key=lambda p: p.get("threads") or 0,
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 6:
            filtered.sort(
                key=lambda p: str(p.get("user") or "").lower(),
                reverse=self.sort_reverse,
            )

        elif self.sort_column == 7:
            filtered.sort(
                key=lambda p: str(p.get("status") or "").lower(),
                reverse=self.sort_reverse,
            )

        self.table.setRowCount(len(filtered))

        for row, process in enumerate(filtered):

            values = [
                str(process.get("pid") or ""),
                str(process.get("name") or "Unknown"),
                f"{process.get('cpu_percent', 0):.1f}%",
                format_bytes(process.get("memory_bytes", 0)),
                f"{process.get('memory_percent', 0):.1f}%",
                str(process.get("threads") or 0),
                str(process.get("user") or "Unknown"),
                str(process.get("status") or "Unknown"),
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)

                if column in (0, 2, 3, 4, 5):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                self.table.setItem(row, column, item)

        self.count_label.setText(
            f"{len(filtered)} of {len(self.processes)} processes"
        )

    def end_selected_process(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "No Process Selected",
                "Select a process first.",
            )
            return

        pid_item = self.table.item(row, 0)

        if pid_item is None:
            return

        try:
            pid = int(pid_item.text())
        except ValueError:
            return

        name_item = self.table.item(row, 1)
        name = name_item.text() if name_item else "this process"

        answer = QMessageBox.question(
            self,
            "End Process",
            f"Are you sure you want to end {name} (PID {pid})?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if terminate_process(pid):
            self.refresh_processes()
        else:
            QMessageBox.warning(
                self,
                "Unable to End Process",
                "SysFlow could not terminate this process. "
                "It may require administrator privileges or may have already exited.",
            )

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)