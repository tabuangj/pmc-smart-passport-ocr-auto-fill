import sys, json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QPlainTextEdit, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from ocr_passport import extract_from_image

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

class OCRWorker(QThread):
    done = Signal(dict)
    def __init__(self, path: str):
        super().__init__()
        self.path = path
    def run(self):
        try:
            data = extract_from_image(self.path) or {}
        except Exception as e:
            data = {"error": str(e)}
        self.done.emit(data)

class DropArea(QLabel):
    fileDropped = Signal(str)
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setText("📄 วางไฟล์พาสปอร์ตที่นี่ หรือคลิก Browse…")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #8c8c8c; border-radius: 14px;
                padding: 22px; font-size: 14px; color: #555; background: #fafafa;
            }
            QLabel:hover { border-color: #666; }
        """)
    def dragEnterEvent(self, e):
        if not e.mimeData().hasUrls():
            e.ignore(); return
        for url in e.mimeData().urls():
            if Path(url.toLocalFile()).suffix.lower() in ALLOWED_EXT:
                e.acceptProposedAction(); return
        e.ignore()
    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in ALLOWED_EXT and p.exists():
                self.fileDropped.emit(str(p)); break

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Passport OCR (No Preview)")
        self.setMinimumSize(700, 440)

        root = QWidget(); self.setCentralWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(16,16,16,16); v.setSpacing(10)

        self.drop = DropArea(); v.addWidget(self.drop)

        row = QHBoxLayout()
        self.btn_browse = QPushButton("Browse…")
        row.addWidget(self.btn_browse)
        row.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        v.addLayout(row)

        self.output = QPlainTextEdit(); self.output.setReadOnly(True)
        self.output.setPlaceholderText("ผลลัพธ์ OCR จะอยู่ที่นี่ (JSON)")
        v.addWidget(self.output)

        self.status = QLabel("Ready.")
        v.addWidget(self.status)

        self.drop.fileDropped.connect(self.start_ocr)
        self.btn_browse.clicked.connect(self.browse)

        self.worker = None

    def browse(self):
        fn, _ = QFileDialog.getOpenFileName(
            self, "เลือกไฟล์พาสปอร์ต", "", "Images (*.jpg *.jpeg *.png *.tif *.tiff)"
        )
        if fn:
            self.start_ocr(fn)

    def start_ocr(self, path: str):
        if not Path(path).exists():
            QMessageBox.warning(self, "File not found", f"ไม่พบไฟล์:\n{path}")
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Processing", "กำลังประมวลผลไฟล์ก่อนหน้าอยู่…")
            return

        self.status.setText(f"OCR… {path}")
        self.output.clear()
        self.btn_browse.setEnabled(False)
        self.drop.setEnabled(False)

        self.worker = OCRWorker(path)
        self.worker.done.connect(self.on_ocr_done)
        self.worker.start()

    def on_ocr_done(self, data: dict):
        self.status.setText("Done.")
        self.btn_browse.setEnabled(True)
        self.drop.setEnabled(True)

        self.output.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        if "error" in data and data["error"]:
            QMessageBox.warning(self, "OCR error", str(data["error"]))

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
