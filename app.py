import re
import sys
import time
from dataclasses import dataclass

import cv2
import mss
import numpy as np
import pyperclip
import pytesseract
from PyQt5.QtCore import QObject, QPoint, QRect, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class MonitorConfig:
    bbox: dict
    threshold: int
    regex_pattern: str
    psm: int
    interval_ms: int


class CaptureWorker(QObject):
    code_found = pyqtSignal(str)
    status = pyqtSignal(str)
    preview = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, config: MonitorConfig) -> None:
        super().__init__()
        self.config = config
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self.status.emit("Monitoring started...")
        pattern = re.compile(self.config.regex_pattern)
        tesseract_cfg = (
            f"--oem 3 --psm {self.config.psm} "
            "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        with mss.mss() as sct:
            while self._running:
                shot = sct.grab(self.config.bbox)
                frame = np.array(shot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, self.config.threshold, 255, cv2.THRESH_BINARY)

                raw_text = pytesseract.image_to_string(thresh, config=tesseract_cfg).upper().strip()
                clean = re.sub(r"[^A-Z0-9\s]", " ", raw_text)
                self.preview.emit(clean)

                match = pattern.search(clean)
                if match:
                    code = match.group(0)
                    self.code_found.emit(code)
                    self.status.emit(f"Code detected: {code}")
                    break

                time.sleep(self.config.interval_ms / 1000)

        self.finished.emit()


class RegionSelector(QWidget):
    region_selected = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        self.origin = QPoint()
        self.current = QPoint()
        self.dragging = False

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setBrush(Qt.transparent)
        painter.fillRect(self.rect(), Qt.transparent)

        if self.dragging or not self.origin.isNull():
            rect = QRect(self.origin, self.current).normalized()
            pen = QPen(Qt.red, 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.current = event.pos()
            self.dragging = True
            self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.dragging:
            self.current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.current = event.pos()
            rect = QRect(self.origin, self.current).normalized()
            if rect.width() > 5 and rect.height() > 5:
                self.region_selected.emit(
                    {
                        "left": rect.x(),
                        "top": rect.y(),
                        "width": rect.width(),
                        "height": rect.height(),
                    }
                )
            self.close()


class PromoMonitorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ultra-fast Promo Code Monitor")
        self.setMinimumSize(640, 400)

        self.bbox = None
        self.worker_thread = None
        self.worker = None

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.box_label = QLabel("ROI: Not selected")
        self.box_label.setStyleSheet("font-size: 16px;")

        self.big_code = QLabel("-----")
        self.big_code.setAlignment(Qt.AlignCenter)
        self.big_code.setStyleSheet("font-size: 64px; font-weight: bold; color: #00aa00;")

        self.status_label = QLabel("Ready")
        self.preview_label = QLabel("OCR preview: ")

        controls = QHBoxLayout()
        self.select_btn = QPushButton("Select ROI")
        self.start_btn = QPushButton("Start Monitoring")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        self.threshold_input = QLineEdit("170")
        self.threshold_input.setMaximumWidth(80)
        self.psm_input = QLineEdit("7")
        self.psm_input.setMaximumWidth(60)
        self.regex_input = QLineEdit(r"\b[A-Z0-9]{5,7}\b")

        controls.addWidget(self.select_btn)
        controls.addWidget(QLabel("Threshold:"))
        controls.addWidget(self.threshold_input)
        controls.addWidget(QLabel("PSM:"))
        controls.addWidget(self.psm_input)
        controls.addWidget(QLabel("Regex:"))
        controls.addWidget(self.regex_input)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)

        layout.addWidget(self.box_label)
        layout.addLayout(controls)
        layout.addWidget(self.big_code)
        layout.addWidget(self.status_label)
        layout.addWidget(self.preview_label)

        self.select_btn.clicked.connect(self.open_selector)
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)

    def open_selector(self) -> None:
        self.status_label.setText("Drag a rectangle around the promo code area...")
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self._set_bbox)
        self.selector.show()

    def _set_bbox(self, bbox: dict) -> None:
        self.bbox = bbox
        self.box_label.setText(f"ROI: {bbox}")
        self.status_label.setText("ROI selected.")

    def start_monitoring(self) -> None:
        if not self.bbox:
            self.status_label.setText("Please select ROI first.")
            return

        try:
            threshold = int(self.threshold_input.text())
            psm = int(self.psm_input.text())
        except ValueError:
            self.status_label.setText("Threshold and PSM must be integers.")
            return

        regex_pattern = self.regex_input.text().strip() or r"\b[A-Z0-9]{5,7}\b"
        config = MonitorConfig(
            bbox=self.bbox,
            threshold=threshold,
            regex_pattern=regex_pattern,
            psm=psm,
            interval_ms=15,
        )

        self.worker_thread = QThread()
        self.worker = CaptureWorker(config)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.code_found.connect(self.on_code_found)
        self.worker.status.connect(self.status_label.setText)
        self.worker.preview.connect(lambda txt: self.preview_label.setText(f"OCR preview: {txt}"))
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self._thread_stopped)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.worker_thread.start()

    def stop_monitoring(self) -> None:
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Stopping...")

    def _thread_stopped(self) -> None:
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_code_found(self, code: str) -> None:
        pyperclip.copy(code)
        self.big_code.setText(code)
        self.big_code.setStyleSheet("font-size: 72px; font-weight: 900; color: #ff1111;")
        self.play_alert()
        self.status_label.setText(f"MATCH! Copied to clipboard: {code}. Monitoring paused.")
        self.stop_monitoring()

    def play_alert(self) -> None:
        app = QGuiApplication.instance()
        if app:
            app.beep()

        try:
            import winsound

            winsound.Beep(2400, 700)
            winsound.Beep(2800, 700)
        except Exception:
            pass


def main() -> None:
    app = QApplication(sys.argv)
    window = PromoMonitorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
