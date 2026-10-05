import sys
import psutil

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPointF,
    QThread,
    Signal,
    QObject,
    Slot,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
    QStackedWidget,
    QScrollArea,
)

from core.system_metrics import (
    get_cpu_usage,
    get_cpu_frequency,
    get_memory,
    get_cpu_per_core,
    get_cpu_temperature,
    get_cpu_temperature_sensors,
)

from core.gpu import get_gpu_info

from pages.performance import PerformancePage
from pages.processes import ProcessesPage
from pages.system_info import SystemInfoPage
from pages.startup import StartupPage
from pages.users import UsersPage
from pages.services import ServicesPage
from pages.power_freq import PowerFreqPage
from pages.benchmarks import BenchmarksPage
from pages.installed_apps import InstalledAppsPage
from pages.disk_space import DiskSpacePage


# =========================================================
# Background Telemetry Worker
# =========================================================

class MetricsWorker(QObject):

    metrics_ready = Signal(dict)

    @Slot()
    def collect(self):

        try:
            cpu = get_cpu_usage()

            frequency = get_cpu_frequency()

            memory = get_memory()

            cores = get_cpu_per_core()

            cpu_temperature = (
                get_cpu_temperature()
            )

            temperature_sensors = (
                get_cpu_temperature_sensors()
            )

            gpu = get_gpu_info()

            self.metrics_ready.emit({
                "cpu": cpu,
                "frequency": frequency,
                "memory": memory,
                "cores": cores,
                "cpu_temperature":
                    cpu_temperature,
                "temperature_sensors":
                    temperature_sensors,
                "gpu": gpu,
            })

        except Exception as error:

            self.metrics_ready.emit({
                "error": str(error)
            })


# =========================================================
# Graph
# =========================================================

class LineGraph(QWidget):

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

        self.setMinimumHeight(
            180
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_OpaquePaintEvent
        )

    def add_value(self, value):

        if value is None:
            return

        try:
            value = float(value)

        except (
            TypeError,
            ValueError,
        ):
            return

        self.values.append(
            value
        )

        if len(self.values) > 60:
            self.values.pop(0)

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        width = self.width()
        height = self.height()

        painter.setBrush(
            QColor("#15181e")
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

        graph_width = (
            right - left
        )

        graph_height = (
            bottom - top
        )

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
                + graph_height * i / 4
            )

            painter.drawLine(
                left,
                int(y),
                right,
                int(y),
            )

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
                        len(self.values) - 1
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
# Metric Card
# =========================================================

class MetricCard(QFrame):

    def __init__(
        self,
        title,
        value="--",
        subtitle="",
    ):

        super().__init__()

        self.setObjectName(
            "metricCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "metricTitle"
        )

        self.value_label = QLabel(
            value
        )

        self.value_label.setObjectName(
            "metricValue"
        )

        self.subtitle_label = QLabel(
            subtitle
        )

        self.subtitle_label.setObjectName(
            "metricSubtitle"
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

    def set_value(self, value):

        self.value_label.setText(
            str(value)
        )

    def set_subtitle(self, text):

        self.subtitle_label.setText(
            str(text)
        )


# =========================================================
# Temperature Row
# =========================================================

class TemperatureRow(QFrame):

    def __init__(
        self,
        name,
        temperature,
    ):

        super().__init__()

        self.setObjectName(
            "temperatureRow"
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        self.name_label = QLabel(
            name
        )

        self.name_label.setObjectName(
            "temperatureName"
        )

        self.temperature_label = QLabel(
            temperature
        )

        self.temperature_label.setObjectName(
            "temperatureValue"
        )

        layout.addWidget(
            self.name_label
        )

        layout.addStretch()

        layout.addWidget(
            self.temperature_label
        )

    def set_temperature(
        self,
        temperature,
    ):

        self.temperature_label.setText(
            temperature
        )


# =========================================================
# SysFlow Main Window
# =========================================================

class SysFlow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "SysFlow"
        )

        self.resize(
            1250,
            850,
        )

        self.setMinimumSize(
            950,
            650,
        )

        self.nav_buttons = {}

        self.core_graphs = []

        self.temperature_rows = []

        self.is_fullscreen = False

        # -------------------------------------------------
        # Telemetry worker
        # -------------------------------------------------

        self.metrics_thread = QThread(
            self
        )

        self.metrics_worker = (
            MetricsWorker()
        )

        self.metrics_worker.moveToThread(
            self.metrics_thread
        )

        # FIX: connect telemetry results to Summary
        self.metrics_worker.metrics_ready.connect(
            self.apply_metrics
        )

        self.metrics_thread.start()

        # -------------------------------------------------
        # UI
        # -------------------------------------------------

        self.setup_ui()

        # -------------------------------------------------
        # Telemetry timer
        # -------------------------------------------------

        self.metrics_timer = QTimer(
            self
        )

        self.metrics_timer.timeout.connect(
            self.request_metrics
        )

        self.metrics_timer.start(
            1000
        )

        self.request_metrics()

    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        # =================================================
        # Sidebar
        # =================================================

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            215
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            12,
            18,
            12,
            18,
        )

        sidebar_layout.setSpacing(
            4
        )

        logo = QLabel(
            "SYSFLOW"
        )

        logo.setObjectName(
            "logo"
        )

        sidebar_layout.addWidget(
            logo
        )

        sidebar_layout.addSpacing(
            20
        )

        overview = QLabel(
            "OVERVIEW"
        )

        overview.setObjectName(
            "sectionLabel"
        )

        sidebar_layout.addWidget(
            overview
        )

        overview_pages = [
            "Summary",
            "Performance",
            "Processes",
            "System Info",
            "Startup Apps",
            "Users",
            "Services",
        ]

        for name in overview_pages:

            self.add_nav_button(
                sidebar_layout,
                name,
            )

        sidebar_layout.addSpacing(
            18
        )

        advanced = QLabel(
            "ADVANCED"
        )

        advanced.setObjectName(
            "sectionLabel"
        )

        sidebar_layout.addWidget(
            advanced
        )

        advanced_pages = [
            "Power & Freq",
            "Benchmarks",
            "Installed Apps",
            "Disk Space",
        ]

        for name in advanced_pages:

            self.add_nav_button(
                sidebar_layout,
                name,
            )

        sidebar_layout.addStretch()

        version = QLabel(
            "SysFlow v0.1"
        )

        version.setObjectName(
            "version"
        )

        sidebar_layout.addWidget(
            version
        )

        # =================================================
        # Pages
        # =================================================

        self.pages = QStackedWidget()

        self.summary_page = (
            self.create_summary_page()
        )

        self.pages.addWidget(
            self.summary_page
        )

        self.page_objects = {
            "Summary":
                self.summary_page,

            "Performance":
                PerformancePage(),

            "Processes":
                ProcessesPage(),

            "System Info":
                SystemInfoPage(),

            "Startup Apps":
                StartupPage(),

            "Users":
                UsersPage(),

            "Services":
                ServicesPage(),

            "Power & Freq":
                PowerFreqPage(),

            "Benchmarks":
                BenchmarksPage(),

            "Installed Apps":
                InstalledAppsPage(),

            "Disk Space":
                DiskSpacePage(),
        }

        for name, page in (
            self.page_objects.items()
        ):

            if name == "Summary":
                continue

            self.pages.addWidget(
                page
            )

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            self.pages
        )

        self.select_page(
            "Summary"
        )

    # =====================================================
    # Summary
    # =====================================================

    def create_summary_page(
        self
    ):

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

        content = QWidget()

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            28,
            22,
            28,
            22,
        )

        content_layout.setSpacing(
            14
        )

        # Header

        header = QHBoxLayout()

        title = QLabel(
            "Summary"
        )

        title.setObjectName(
            "pageTitle"
        )

        live = QLabel(
            "● LIVE"
        )

        live.setObjectName(
            "live"
        )

        header.addWidget(
            title
        )

        header.addStretch()

        header.addWidget(
            live
        )

        content_layout.addLayout(
            header
        )

        # Cards

        cards = QHBoxLayout()

        cards.setSpacing(
            12
        )

        self.cpu_card = MetricCard(
            "CPU",
            "--",
            "Loading...",
        )

        self.memory_card = MetricCard(
            "MEMORY",
            "--",
            "Loading...",
        )

        self.temperature_card = (
            MetricCard(
                "CPU TEMP",
                "--",
                "Loading...",
            )
        )

        gpu = get_gpu_info()

        gpu_name = gpu.get(
            "name",
            "GPU unavailable",
        )

        gpu_name = self.clean_gpu_name(
            gpu_name
        )

        self.gpu_card = MetricCard(
            "GPU",
            gpu_name,
            "Detected hardware",
        )

        cards.addWidget(
            self.cpu_card
        )

        cards.addWidget(
            self.memory_card
        )

        cards.addWidget(
            self.temperature_card
        )

        cards.addWidget(
            self.gpu_card
        )

        content_layout.addLayout(
            cards
        )

        # CPU graph

        self.cpu_graph = LineGraph(
            "CPU UTILIZATION",
            100,
            "%",
        )

        content_layout.addWidget(
            self.cpu_graph
        )

        # Logical processors

        core_title = QLabel(
            "LOGICAL PROCESSORS"
        )

        core_title.setObjectName(
            "sectionTitle"
        )

        content_layout.addWidget(
            core_title
        )

        self.core_grid = QGridLayout()

        self.core_grid.setSpacing(
            12
        )

        content_layout.addLayout(
            self.core_grid
        )

        core_count = (
            psutil.cpu_count(
                logical=True
            )
            or 1
        )

        for core_index in range(
            core_count
        ):

            graph = LineGraph(
                f"CORE {core_index}",
                100,
                "%",
            )

            self.core_graphs.append(
                graph
            )

            row = core_index // 2
            column = core_index % 2

            self.core_grid.addWidget(
                graph,
                row,
                column,
            )

        # Temperature

        temperature_title = QLabel(
            "CPU TEMPERATURES"
        )

        temperature_title.setObjectName(
            "sectionTitle"
        )

        content_layout.addWidget(
            temperature_title
        )

        self.temperature_container = (
            QFrame()
        )

        self.temperature_container.setObjectName(
            "temperatureContainer"
        )

        self.temperature_layout = (
            QVBoxLayout(
                self.temperature_container
            )
        )

        self.temperature_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.temperature_layout.setSpacing(
            4
        )

        content_layout.addWidget(
            self.temperature_container
        )

        # Memory

        memory_title = QLabel(
            "MEMORY"
        )

        memory_title.setObjectName(
            "sectionTitle"
        )

        content_layout.addWidget(
            memory_title
        )

        self.memory_graph = LineGraph(
            "MEMORY UTILIZATION",
            100,
            "%",
        )

        content_layout.addWidget(
            self.memory_graph
        )

        # GPU

        self.gpu_graph = LineGraph(
            "GPU UTILIZATION",
            100,
            "%",
        )

        self.gpu_graph.setVisible(
            False
        )

        content_layout.addWidget(
            self.gpu_graph
        )

        self.gpu_status = QLabel(
            "GPU telemetry unavailable"
        )

        self.gpu_status.setObjectName(
            "telemetryStatus"
        )

        content_layout.addWidget(
            self.gpu_status
        )

        # Bottom bars

        bars = QHBoxLayout()

        bars.setSpacing(
            12
        )

        cpu_panel = QFrame()

        cpu_panel.setObjectName(
            "infoPanel"
        )

        cpu_layout = QVBoxLayout(
            cpu_panel
        )

        cpu_label = QLabel(
            "CPU LOAD"
        )

        cpu_label.setObjectName(
            "panelTitle"
        )

        self.cpu_bar = QProgressBar()

        self.cpu_bar.setRange(
            0,
            100,
        )

        self.cpu_bar.setTextVisible(
            False
        )

        self.cpu_bar.setFixedHeight(
            8
        )

        cpu_layout.addWidget(
            cpu_label
        )

        cpu_layout.addWidget(
            self.cpu_bar
        )

        memory_panel = QFrame()

        memory_panel.setObjectName(
            "infoPanel"
        )

        memory_layout = QVBoxLayout(
            memory_panel
        )

        memory_label = QLabel(
            "MEMORY LOAD"
        )

        memory_label.setObjectName(
            "panelTitle"
        )

        self.memory_bar = QProgressBar()

        self.memory_bar.setRange(
            0,
            100,
        )

        self.memory_bar.setTextVisible(
            False
        )

        self.memory_bar.setFixedHeight(
            8
        )

        memory_layout.addWidget(
            memory_label
        )

        memory_layout.addWidget(
            self.memory_bar
        )

        bars.addWidget(
            cpu_panel
        )

        bars.addWidget(
            memory_panel
        )

        content_layout.addLayout(
            bars
        )

        content_layout.addStretch()

        scroll.setWidget(
            content
        )

        return scroll

    # =====================================================
    # Navigation
    # =====================================================

    def add_nav_button(
        self,
        layout,
        text,
    ):

        button = QPushButton(
            text
        )

        button.setObjectName(
            "navButton"
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            lambda checked=False,
            name=text:
            self.select_page(name)
        )

        self.nav_buttons[text] = button

        layout.addWidget(
            button
        )

    def select_page(
        self,
        name,
    ):

        page = self.page_objects.get(
            name
        )

        if page is None:
            return

        self.pages.setCurrentWidget(
            page
        )

        self.set_nav_selected(
            name
        )

    def set_nav_selected(
        self,
        name,
    ):

        for (
            page_name,
            button,
        ) in self.nav_buttons.items():

            button.setProperty(
                "selected",
                page_name == name,
            )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

            button.update()

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def clean_gpu_name(name):

        return (
            name.replace(
                "NVIDIA Corporation ",
                "",
            )
            .replace(
                "Intel Corporation ",
                "",
            )
            .replace(
                "Advanced Micro Devices, Inc. ",
                "",
            )
        )

    # =====================================================
    # Temperature
    # =====================================================

    def update_temperature_list(
        self,
        sensors,
    ):

        if not sensors:

            if not self.temperature_rows:

                row = TemperatureRow(
                    "CPU temperature",
                    "Unavailable",
                )

                self.temperature_rows.append(
                    row
                )

                self.temperature_layout.addWidget(
                    row
                )

            return

        while len(
            self.temperature_rows
        ) < len(sensors):

            index = len(
                self.temperature_rows
            )

            sensor = sensors[index]

            row = TemperatureRow(
                sensor.get(
                    "label",
                    sensor.get(
                        "sensor",
                        "Sensor",
                    ),
                ),
                "Unavailable",
            )

            self.temperature_rows.append(
                row
            )

            self.temperature_layout.addWidget(
                row
            )

        for index, sensor in enumerate(
            sensors
        ):

            if index >= len(
                self.temperature_rows
            ):
                break

            temperature = sensor.get(
                "temperature"
            )

            if temperature is None:

                text = "Unavailable"

            else:

                text = (
                    f"{temperature:.1f}°C"
                )

            self.temperature_rows[
                index
            ].name_label.setText(
                sensor.get(
                    "label",
                    sensor.get(
                        "sensor",
                        "Sensor",
                    ),
                )
            )

            self.temperature_rows[
                index
            ].set_temperature(
                text
            )

    # =====================================================
    # Telemetry
    # =====================================================

    def request_metrics(
        self
    ):

        # Use a short-lived Python thread so
        # psutil/lspci telemetry does not freeze
        # the Qt GUI.

        import threading

        thread = threading.Thread(
            target=self.metrics_worker.collect,
            daemon=True,
        )

        thread.start()

    def apply_metrics(
        self,
        data,
    ):

        if "error" in data:
            return

        cpu = data.get(
            "cpu"
        )

        frequency = data.get(
            "frequency"
        )

        if cpu is not None:

            self.cpu_card.set_value(
                f"{cpu:.1f}%"
            )

            self.cpu_bar.setValue(
                max(
                    0,
                    min(
                        int(cpu),
                        100,
                    ),
                )
            )

            self.cpu_graph.add_value(
                cpu
            )

        if frequency is not None:

            self.cpu_card.set_subtitle(
                f"{frequency / 1000:.2f} GHz"
            )

        else:

            self.cpu_card.set_subtitle(
                "Frequency unavailable"
            )

        cores = data.get(
            "cores",
            [],
        )

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

        temperature = data.get(
            "cpu_temperature"
        )

        if temperature is None:

            self.temperature_card.set_value(
                "--"
            )

            self.temperature_card.set_subtitle(
                "Temperature unavailable"
            )

        else:

            self.temperature_card.set_value(
                f"{temperature:.1f}°C"
            )

            self.temperature_card.set_subtitle(
                "CPU temperature"
            )

        self.update_temperature_list(
            data.get(
                "temperature_sensors",
                [],
            )
        )

        memory = data.get(
            "memory"
        )

        if memory:

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

            self.memory_card.set_value(
                f"{percent:.1f}%"
            )

            self.memory_card.set_subtitle(
                f"{used_gb:.1f} GB / "
                f"{total_gb:.1f} GB"
            )

            self.memory_bar.setValue(
                max(
                    0,
                    min(
                        int(percent),
                        100,
                    ),
                )
            )

            self.memory_graph.add_value(
                percent
            )

        gpu = data.get(
            "gpu",
            {},
        )

        gpu_name = self.clean_gpu_name(
            gpu.get(
                "name",
                "GPU unavailable",
            )
        )

        self.gpu_card.set_value(
            gpu_name
        )

        utilization = gpu.get(
            "utilization"
        )

        gpu_temperature = gpu.get(
            "temperature"
        )

        if utilization is not None:

            self.gpu_graph.setVisible(
                True
            )

            self.gpu_status.setVisible(
                False
            )

            self.gpu_graph.add_value(
                utilization
            )

            details = (
                f"{utilization:.1f}% utilization"
            )

            if gpu_temperature is not None:

                details += (
                    f" • "
                    f"{gpu_temperature:.0f}°C"
                )

            self.gpu_card.set_subtitle(
                details
            )

        else:

            self.gpu_graph.setVisible(
                False
            )

            self.gpu_status.setVisible(
                True
            )

            self.gpu_status.setText(
                "GPU telemetry unavailable "
                "on this system"
            )

            self.gpu_card.set_subtitle(
                "Hardware detected • "
                "telemetry unavailable"
            )

    # =====================================================
    # Keyboard shortcuts
    # =====================================================

    def keyPressEvent(
        self,
        event,
    ):

        if (
            event.key()
            == Qt.Key.Key_F11
        ):

            self.toggle_fullscreen()

            return

        if (
            event.key()
            == Qt.Key.Key_Escape
            and self.is_fullscreen
        ):

            self.toggle_fullscreen()

            return

        super().keyPressEvent(
            event
        )

    def toggle_fullscreen(self):

        if self.is_fullscreen:

            self.showNormal()

            self.is_fullscreen = False

        else:

            self.showFullScreen()

            self.is_fullscreen = True

    # =====================================================
    # Cleanup
    # =====================================================

    def closeEvent(
        self,
        event,
    ):

        self.metrics_timer.stop()

        self.metrics_thread.quit()

        self.metrics_thread.wait(
            2000
        )

        super().closeEvent(
            event
        )


# =========================================================
# Application
# =========================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "SysFlow"
    )

    app.setApplicationDisplayName(
        "SysFlow"
    )

    app.setOrganizationName(
        "SysFlow"
    )

    app.setFont(
        QFont(
            "Sans",
            10,
        )
    )

    app.setStyleSheet("""
        QMainWindow {
            background: #0c0e12;
        }

        QWidget {
            color: #e5e7eb;
            font-family: Arial;
        }

        QScrollArea {
            background: #0c0e12;
            border: none;
        }

        QScrollBar:vertical {
            background: #0c0e12;
            width: 10px;
            margin: 2px;
        }

        QScrollBar::handle:vertical {
            background: #30353e;
            min-height: 35px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #414752;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }

        #sidebar {
            background: #101217;
            border-right: 1px solid #24272e;
        }

        #logo {
            font-size: 21px;
            font-weight: bold;
            letter-spacing: 2px;
            color: #ffffff;
        }

        #sectionLabel {
            color: #686d78;
            font-size: 10px;
            font-weight: bold;
            padding-left: 8px;
        }

        #navButton {
            text-align: left;
            padding: 9px 10px;
            border-radius: 6px;
            border: none;
            color: #9da2ad;
            background: transparent;
        }

        #navButton:hover {
            background: #1b1e25;
            color: #ffffff;
        }

        #navButton[selected="true"] {
            background: #20252e;
            color: #ffffff;
        }

        #version {
            color: #555a64;
            font-size: 10px;
            padding-left: 8px;
        }

        #pageTitle {
            font-size: 25px;
            font-weight: bold;
            color: #ffffff;
        }

        #live {
            color: #55d68a;
            font-size: 11px;
            font-weight: bold;
        }

        #metricCard {
            background: #15181e;
            border: 1px solid #252932;
            border-radius: 10px;
        }

        #metricTitle {
            color: #777c87;
            font-size: 10px;
            font-weight: bold;
        }

        #metricValue {
            color: #f4f5f7;
            font-size: 22px;
            font-weight: bold;
        }

        #metricSubtitle {
            color: #777c87;
            font-size: 10px;
        }

        #temperatureContainer {
            background: #15181e;
            border: 1px solid #252932;
            border-radius: 10px;
        }

        #temperatureRow {
            background: #1a1d23;
            border: 1px solid #252932;
            border-radius: 6px;
        }

        #temperatureName {
            color: #aeb4bf;
            font-size: 12px;
        }

        #temperatureValue {
            color: #f4f5f7;
            font-size: 13px;
            font-weight: bold;
        }

        #telemetryStatus {
            color: #686d78;
            font-size: 10px;
            padding-left: 4px;
        }

        #infoPanel {
            background: #15181e;
            border: 1px solid #252932;
            border-radius: 8px;
            padding: 4px;
        }

        #panelTitle {
            color: #777c87;
            font-size: 10px;
            font-weight: bold;
        }

        QProgressBar {
            background: #252932;
            border: none;
            border-radius: 4px;
        }

        QProgressBar::chunk {
            background: #5aa9ff;
            border-radius: 4px;
        }
    """)

    window = SysFlow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()