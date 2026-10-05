import math
import os
import time
import threading

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QProgressBar,
)


def integer_benchmark(iterations):
    """
    CPU integer workload.

    Returns the final value so the Python interpreter
    cannot trivially discard the calculation.
    """

    value = 0x12345678

    for i in range(iterations):
        value ^= (i * 2654435761) & 0xFFFFFFFF
        value = (
            (value << 5)
            | (value >> 27)
        ) & 0xFFFFFFFF

        value = (
            value * 1664525
            + 1013904223
        ) & 0xFFFFFFFF

    return value


def floating_benchmark(iterations):
    """
    Floating-point CPU workload.
    """

    value = 1.000001

    for i in range(iterations):
        value = (
            math.sin(value)
            + math.cos(value)
            + math.sqrt(
                abs(value) + 1.0
            )
        )

        value *= 1.0000001

        if value > 1000000:
            value /= 1000000

    return value


def run_single_integer():
    iterations = 1_000_000

    start = time.perf_counter()

    result = integer_benchmark(
        iterations
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return elapsed, result


def run_single_float():
    iterations = 250_000

    start = time.perf_counter()

    result = floating_benchmark(
        iterations
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return elapsed, result


def run_worker_integer():
    iterations = 2_000_000

    start = time.perf_counter()

    result = integer_benchmark(
        iterations
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return elapsed, result


def run_worker_float():
    iterations = 500_000

    start = time.perf_counter()

    result = floating_benchmark(
        iterations
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return elapsed, result


class BenchmarkWorker(QObject):

    finished = Signal(dict)
    progress = Signal(int)
    error = Signal(str)

    @Slot()
    def run(self):

        try:
            self.progress.emit(5)

            single_integer_time, _ = (
                run_single_integer()
            )

            self.progress.emit(25)

            single_float_time, _ = (
                run_single_float()
            )

            self.progress.emit(45)

            cpu_count = (
                os.cpu_count()
                or 1
            )

            results = [None] * cpu_count

            def worker(index):
                results[index] = (
                    run_worker_integer()[0]
                )

            threads = []

            start = time.perf_counter()

            for index in range(cpu_count):

                thread = threading.Thread(
                    target=worker,
                    args=(index,),
                )

                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            multi_integer_time = (
                time.perf_counter()
                - start
            )

            self.progress.emit(70)

            results = [None] * cpu_count

            def float_worker(index):
                results[index] = (
                    run_worker_float()[0]
                )

            threads = []

            start = time.perf_counter()

            for index in range(cpu_count):

                thread = threading.Thread(
                    target=float_worker,
                    args=(index,),
                )

                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            multi_float_time = (
                time.perf_counter()
                - start
            )

            self.progress.emit(95)

            single_integer_score = (
                1000
                / max(
                    single_integer_time,
                    0.000001,
                )
            )

            single_float_score = (
                1000
                / max(
                    single_float_time,
                    0.000001,
                )
            )

            multi_integer_score = (
                1000
                / max(
                    multi_integer_time,
                    0.000001,
                )
            )

            multi_float_score = (
                1000
                / max(
                    multi_float_time,
                    0.000001,
                )
            )

            result = {
                "single_integer_time":
                    single_integer_time,

                "single_float_time":
                    single_float_time,

                "multi_integer_time":
                    multi_integer_time,

                "multi_float_time":
                    multi_float_time,

                "single_integer_score":
                    single_integer_score,

                "single_float_score":
                    single_float_score,

                "multi_integer_score":
                    multi_integer_score,

                "multi_float_score":
                    multi_float_score,
            }

            self.progress.emit(100)

            self.finished.emit(result)

        except Exception as exc:

            self.error.emit(
                str(exc)
            )


class BenchmarkCard(QFrame):

    def __init__(
        self,
        title,
        description,
    ):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        layout.setSpacing(6)

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        description_label = QLabel(
            description
        )

        description_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 12px;
            }
        """)

        self.value_label = QLabel(
            "Not tested"
        )

        self.value_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
            }
        """)

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            description_label
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
            value
        )


class BenchmarksPage(QWidget):

    def __init__(self):
        super().__init__()

        self.thread = None
        self.worker = None

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(16)

        title = QLabel(
            "Benchmarks"
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
            }
        """)

        subtitle = QLabel(
            "Measure local CPU performance using repeatable workloads."
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 14px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        controls = QHBoxLayout()

        self.run_button = QPushButton(
            "Run Benchmark"
        )

        self.run_button.clicked.connect(
            self.start_benchmark
        )

        controls.addWidget(
            self.run_button
        )

        self.status_label = QLabel(
            "Ready"
        )

        self.status_label.setStyleSheet("""
            QLabel {
                color: #8f96a3;
                font-size: 13px;
            }
        """)

        controls.addWidget(
            self.status_label
        )

        controls.addStretch()

        layout.addLayout(
            controls
        )

        self.progress = QProgressBar()

        self.progress.setRange(
            0,
            100,
        )

        self.progress.setValue(0)

        self.progress.setTextVisible(
            False
        )

        layout.addWidget(
            self.progress
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            12
        )

        grid.setVerticalSpacing(
            12
        )

        self.single_integer = (
            BenchmarkCard(
                "Single-thread Integer",
                "Integer arithmetic workload",
            )
        )

        self.single_float = (
            BenchmarkCard(
                "Single-thread Floating Point",
                "Floating-point workload",
            )
        )

        self.multi_integer = (
            BenchmarkCard(
                "Multi-thread Integer",
                "All logical processors",
            )
        )

        self.multi_float = (
            BenchmarkCard(
                "Multi-thread Floating Point",
                "All logical processors",
            )
        )

        grid.addWidget(
            self.single_integer,
            0,
            0,
        )

        grid.addWidget(
            self.single_float,
            0,
            1,
        )

        grid.addWidget(
            self.multi_integer,
            1,
            0,
        )

        grid.addWidget(
            self.multi_float,
            1,
            1,
        )

        layout.addLayout(
            grid
        )

        info = QFrame()

        info_layout = QVBoxLayout(
            info
        )

        info_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        info_title = QLabel(
            "About these scores"
        )

        info_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
            }
        """)

        info_text = QLabel(
            "Higher scores mean the workload completed faster. "
            "Scores are only meaningful when comparing runs of "
            "the same SysFlow benchmark on the same benchmark version."
        )

        info_text.setWordWrap(
            True
        )

        info_text.setStyleSheet("""
            QLabel {
                color: #9da5b3;
                font-size: 13px;
            }
        """)

        info_layout.addWidget(
            info_title
        )

        info_layout.addWidget(
            info_text
        )

        info.setStyleSheet("""
            QFrame {
                background: #15181e;
                border: 1px solid #292e37;
                border-radius: 10px;
            }
        """)

        layout.addWidget(
            info
        )

        layout.addStretch()

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
                font-weight: 600;
            }

            QPushButton:hover {
                background: #22262e;
            }

            QPushButton:disabled {
                color: #666d78;
                background: #16191e;
            }

            QProgressBar {
                background: #1a1d23;
                border: 1px solid #292e37;
                border-radius: 5px;
                height: 8px;
            }

            QProgressBar::chunk {
                background: #5b8cff;
                border-radius: 4px;
            }
        """)

    def start_benchmark(self):

        if self.thread is not None:
            return

        self.run_button.setEnabled(
            False
        )

        self.progress.setValue(0)

        self.status_label.setText(
            "Running benchmark..."
        )

        self.single_integer.set_value(
            "Running..."
        )

        self.single_float.set_value(
            "Waiting..."
        )

        self.multi_integer.set_value(
            "Waiting..."
        )

        self.multi_float.set_value(
            "Waiting..."
        )

        self.thread = QThread()

        self.worker = (
            BenchmarkWorker()
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.progress.setValue
        )

        self.worker.finished.connect(
            self.benchmark_finished
        )

        self.worker.error.connect(
            self.benchmark_error
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.cleanup_thread
        )

        self.thread.start()

    def benchmark_finished(
        self,
        results,
    ):

        self.single_integer.set_value(
            f"{results['single_integer_score']:.0f} points"
        )

        self.single_float.set_value(
            f"{results['single_float_score']:.0f} points"
        )

        self.multi_integer.set_value(
            f"{results['multi_integer_score']:.0f} points"
        )

        self.multi_float.set_value(
            f"{results['multi_float_score']:.0f} points"
        )

        self.status_label.setText(
            "Benchmark complete"
        )

    def benchmark_error(
        self,
        message,
    ):

        self.status_label.setText(
            "Benchmark failed"
        )

        self.single_integer.set_value(
            "Unavailable"
        )

        self.single_float.set_value(
            "Unavailable"
        )

        self.multi_integer.set_value(
            "Unavailable"
        )

        self.multi_float.set_value(
            "Unavailable"
        )

        print(
            "Benchmark error:",
            message,
        )

    def cleanup_thread(self):

        if self.thread is not None:

            self.thread.deleteLater()

        self.thread = None
        self.worker = None

        self.run_button.setEnabled(
            True
        )

    def closeEvent(self, event):

        if self.thread is not None:

            self.thread.quit()
            self.thread.wait(2000)

        super().closeEvent(event)