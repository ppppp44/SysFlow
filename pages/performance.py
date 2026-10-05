from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
)

from core.system_metrics import (
    get_cpu_usage,
    get_cpu_frequency,
    get_memory,
    get_cpu_per_core,
    get_cpu_temperature,
)


# =========================================================
# Graph
# =========================================================

class PerformanceGraph(QWidget):

    def __init__(
        self,
        title,
        maximum=100,
        unit="%",
    ):
        super().__init__()

        self.title = title
        self.maximum = maximum
        self.unit = unit
        self.values = []

        self.setMinimumHeight(190)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def add_value(self, value):

        if value is None:
            return

        try:
            value = float(value)
        except (TypeError, ValueError):
            return

        self.values.append(value)

        if len(self.values) > 90:
            self.values.pop(0)

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        # Background
        painter.setBrush(
            QColor("#111318")
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.drawRoundedRect(
            0,
            0,
            width,
            height,
            10,
            10,
        )

        # Title
        painter.setPen(
            QColor("#d7d9df")
        )

        painter.setFont(
            QFont(
                "Arial",
                10,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            16,
            25,
            self.title,
        )

        if not self.values:

            painter.setPen(
                QColor("#777c87")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    9,
                )
            )

            painter.drawText(
                16,
                height // 2,
                "Collecting measurements...",
            )

            return

        left = 16
        right = width - 16
        top = 42
        bottom = height - 20

        graph_width = right - left
        graph_height = bottom - top

        # Grid
        grid_pen = QPen(
            QColor("#252932")
        )

        grid_pen.setWidth(1)

        painter.setPen(
            grid_pen
        )

        for i in range(5):

            y = (
                top
                + graph_height
                * i
                / 4
            )

            painter.drawLine(
                left,
                int(y),
                right,
                int(y),
            )

        # Graph line
        maximum = max(
            self.maximum,
            1,
        )

        graph_pen = QPen(
            QColor("#5aa9ff")
        )

        graph_pen.setWidth(2)

        painter.setPen(
            graph_pen
        )

        points = []

        for i, value in enumerate(
            self.values
        ):

            if len(self.values) == 1:

                x = left

            else:

                x = (
                    left
                    + graph_width
                    * i
                    / (
                        len(self.values)
                        - 1
                    )
                )

            value = max(
                0,
                min(
                    value,
                    maximum,
                ),
            )

            y = (
                bottom
                - (
                    value
                    / maximum
                    * graph_height
                )
            )

            points.append(
                QPointF(
                    x,
                    y,
                )
            )

        for i in range(
            len(points) - 1
        ):

            painter.drawLine(
                points[i],
                points[i + 1],
            )

        # Current value
        current = self.values[-1]

        painter.setPen(
            QColor("#9ea3ad")
        )

        painter.setFont(
            QFont(
                "Arial",
                9,
            )
        )

        if self.unit == "%":

            text = (
                f"{current:.1f}%"
            )

        elif self.unit == "°C":

            text = (
                f"{current:.1f}°C"
            )

        elif self.unit == "GHz":

            text = (
                f"{current:.2f} GHz"
            )

        else:

            text = (
                f"{current:.1f}"
                f"{self.unit}"
            )

        painter.drawText(
            right - 80,
            25,
            text,
        )


# =========================================================
# Stat Card
# =========================================================

class PerformanceStat(QFrame):

    def __init__(
        self,
        title,
        value="--",
        subtitle="",
    ):
        super().__init__()

        self.setObjectName(
            "performanceStat"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        layout.setSpacing(5)

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "statTitle"
        )

        self.value_label = QLabel(
            value
        )

        self.value_label.setObjectName(
            "statValue"
        )

        self.subtitle_label = QLabel(
            subtitle
        )

        self.subtitle_label.setObjectName(
            "statSubtitle"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.subtitle_label
        )


    def set_value(
        self,
        value,
    ):

        self.value_label.setText(
            value
        )


    def set_subtitle(
        self,
        text,
    ):

        self.subtitle_label.setText(
            text
        )


# =========================================================
# Core Card
# =========================================================

class CoreCard(QFrame):

    def __init__(
        self,
        core_number,
    ):
        super().__init__()

        self.setObjectName(
            "coreCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        layout.setSpacing(
            8
        )

        title = QLabel(
            f"Logical Processor {core_number}"
        )

        title.setObjectName(
            "coreTitle"
        )

        self.graph = PerformanceGraph(
            f"CORE {core_number}",
            100,
            "%",
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.graph
        )


# =========================================================
# Performance Page
# =========================================================

class PerformancePage(QWidget):

    def __init__(self):

        super().__init__()

        self.cpu_graph = None
        self.memory_graph = None
        self.frequency_graph = None
        self.temperature_graph = None

        self.core_graphs = []

        self.setup_ui()

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.update_metrics
        )

        self.timer.start(
            1000
        )

        self.update_metrics()


    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        # -------------------------------------------------
        # Outer page
        # -------------------------------------------------

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        # -------------------------------------------------
        # Scroll area
        # -------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # -------------------------------------------------
        # Scroll content
        # -------------------------------------------------

        content = QWidget()

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            28,
            22,
            28,
            28,
        )

        layout.setSpacing(
            14
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            "Performance"
        )

        title.setObjectName(
            "performanceTitle"
        )

        live = QLabel(
            "● LIVE"
        )

        live.setObjectName(
            "performanceLive"
        )

        header.addWidget(
            title
        )

        header.addStretch()

        header.addWidget(
            live
        )

        layout.addLayout(
            header
        )

        # -------------------------------------------------
        # CPU Stats
        # -------------------------------------------------

        cpu_stats = QGridLayout()

        cpu_stats.setSpacing(
            10
        )

        self.cpu_usage = PerformanceStat(
            "CPU UTILIZATION",
            "--",
            "Overall processor load",
        )

        self.cpu_frequency = PerformanceStat(
            "CPU FREQUENCY",
            "--",
            "Current frequency",
        )

        self.cpu_temperature = PerformanceStat(
            "CPU TEMPERATURE",
            "--",
            "Best available sensor",
        )

        self.logical_processors = PerformanceStat(
            "LOGICAL PROCESSORS",
            "--",
            "Detected processors",
        )

        cpu_stats.addWidget(
            self.cpu_usage,
            0,
            0,
        )

        cpu_stats.addWidget(
            self.cpu_frequency,
            0,
            1,
        )

        cpu_stats.addWidget(
            self.cpu_temperature,
            1,
            0,
        )

        cpu_stats.addWidget(
            self.logical_processors,
            1,
            1,
        )

        cpu_stats.setColumnStretch(
            0,
            1
        )

        cpu_stats.setColumnStretch(
            1,
            1
        )

        layout.addLayout(
            cpu_stats
        )

        # -------------------------------------------------
        # CPU
        # -------------------------------------------------

        cpu_title = QLabel(
            "CPU"
        )

        cpu_title.setObjectName(
            "performanceSection"
        )

        layout.addWidget(
            cpu_title
        )

        self.cpu_graph = PerformanceGraph(
            "CPU UTILIZATION",
            100,
            "%",
        )

        layout.addWidget(
            self.cpu_graph
        )

        # -------------------------------------------------
        # Frequency
        # -------------------------------------------------

        self.frequency_graph = PerformanceGraph(
            "CPU FREQUENCY",
            5,
            "GHz",
        )

        layout.addWidget(
            self.frequency_graph
        )

        # -------------------------------------------------
        # Temperature
        # -------------------------------------------------

        self.temperature_graph = PerformanceGraph(
            "CPU TEMPERATURE",
            110,
            "°C",
        )

        layout.addWidget(
            self.temperature_graph
        )

        # -------------------------------------------------
        # Logical Processors
        # -------------------------------------------------

        core_title = QLabel(
            "LOGICAL PROCESSORS"
        )

        core_title.setObjectName(
            "performanceSection"
        )

        layout.addWidget(
            core_title
        )

        import psutil

        core_count = (
            psutil.cpu_count(
                logical=True
            )
            or 1
        )

        self.logical_processors.set_value(
            str(core_count)
        )

        # Dedicated core grid
        core_grid = QGridLayout()

        core_grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        core_grid.setHorizontalSpacing(
            14
        )

        core_grid.setVerticalSpacing(
            14
        )

        core_grid.setColumnStretch(
            0,
            1
        )

        core_grid.setColumnStretch(
            1,
            1
        )

        for index in range(
            core_count
        ):

            card = CoreCard(
                index
            )

            card.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

            self.core_graphs.append(
                card.graph
            )

            row = index // 2
            column = index % 2

            core_grid.addWidget(
                card,
                row,
                column,
            )

        layout.addLayout(
            core_grid
        )

        # -------------------------------------------------
        # Memory
        # -------------------------------------------------

        memory_title = QLabel(
            "MEMORY"
        )

        memory_title.setObjectName(
            "performanceSection"
        )

        layout.addWidget(
            memory_title
        )

        self.memory_graph = PerformanceGraph(
            "MEMORY UTILIZATION",
            100,
            "%",
        )

        layout.addWidget(
            self.memory_graph
        )

        self.memory_stats = PerformanceStat(
            "MEMORY",
            "--",
            "Used / total",
        )

        layout.addWidget(
            self.memory_stats
        )

        layout.addStretch()

        # -------------------------------------------------
        # Put content inside scroll area
        # -------------------------------------------------

        scroll.setWidget(
            content
        )

        outer_layout.addWidget(
            scroll
        )

        # -------------------------------------------------
        # Styling
        # -------------------------------------------------

        self.setStyleSheet("""
            QWidget {
                background: #111318;
                color: #ffffff;
            }

            QScrollArea {
                background: #111318;
                border: none;
            }

            QScrollBar:vertical {
                background: #111318;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #2b3038;
                border-radius: 5px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background: #3a414c;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QLabel#performanceTitle {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }

            QLabel#performanceLive {
                color: #5aa9ff;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#performanceSection {
                color: #d7d9df;
                font-size: 16px;
                font-weight: 700;
                margin-top: 6px;
            }

            QFrame#performanceStat {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }

            QLabel#statTitle {
                color: #8f96a3;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#statValue {
                color: #ffffff;
                font-size: 23px;
                font-weight: 700;
            }

            QLabel#statSubtitle {
                color: #777e8b;
                font-size: 11px;
            }

            QFrame#coreCard {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 12px;
            }

            QFrame#coreCard:hover {
                border: 1px solid #3a414c;
            }

            QLabel#coreTitle {
                color: #d7d9df;
                font-size: 13px;
                font-weight: 700;
            }
        """)


    # =====================================================
    # Metrics
    # =====================================================

    def update_metrics(
        self
    ):

        # -------------------------------------------------
        # CPU
        # -------------------------------------------------

        cpu = get_cpu_usage()

        self.cpu_usage.set_value(
            f"{cpu:.1f}%"
        )

        self.cpu_graph.add_value(
            cpu
        )

        # -------------------------------------------------
        # Frequency
        # -------------------------------------------------

        frequency = (
            get_cpu_frequency()
        )

        if frequency is not None:

            ghz = frequency / 1000

            self.cpu_frequency.set_value(
                f"{ghz:.2f} GHz"
            )

            self.frequency_graph.add_value(
                ghz
            )

        else:

            self.cpu_frequency.set_value(
                "--"
            )

        # -------------------------------------------------
        # Temperature
        # -------------------------------------------------

        temperature = (
            get_cpu_temperature()
        )

        if temperature is not None:

            self.cpu_temperature.set_value(
                f"{temperature:.1f}°C"
            )

            self.temperature_graph.add_value(
                temperature
            )

        else:

            self.cpu_temperature.set_value(
                "--"
            )

        # -------------------------------------------------
        # Logical Processors
        # -------------------------------------------------

        cores = get_cpu_per_core()

        for index, usage in enumerate(
            cores
        ):

            if index >= len(
                self.core_graphs
            ):
                break

            self.core_graphs[
                index
            ].add_value(
                usage
            )

        # -------------------------------------------------
        # Memory
        # -------------------------------------------------

        memory = get_memory()

        percent = memory[
            "percent"
        ]

        used_gb = (
            memory["used"]
            / (1024 ** 3)
        )

        total_gb = (
            memory["total"]
            / (1024 ** 3)
        )

        self.memory_graph.add_value(
            percent
        )

        self.memory_stats.set_value(
            f"{percent:.1f}%"
        )

        self.memory_stats.set_subtitle(
            f"{used_gb:.1f} GB / "
            f"{total_gb:.1f} GB"
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