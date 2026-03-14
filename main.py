"""RawriisSTT — entry point.

Run via:
  launcher.py   — from source on any platform (auto-installs deps)
  main.py       — directly, if deps are already installed
  RawriisSTT.exe — Windows bundle built with PyInstaller
"""

from __future__ import annotations

import logging
import sys
import traceback

_FROZEN = getattr(sys, "frozen", False)

if _FROZEN:
    # When running as a PyInstaller bundle, write all output to a log file
    # next to the exe so crashes are always captured even if the console closes.
    import os
    from pathlib import Path
    _log_path = Path(sys.executable).parent / "RawriisSTT.log"
    _log_file = open(_log_path, "w", encoding="utf-8", buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file
    _log_kwargs: dict = dict(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=_log_file,
        force=True,
    )
else:
    _log_kwargs = dict(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

logging.basicConfig(**_log_kwargs)

# comtypes regenerates COM type stubs on every cold start inside a frozen bundle.
# The INFO chatter is harmless; suppress it so it doesn't pollute the log.
logging.getLogger("comtypes").setLevel(logging.WARNING)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QPalette, QIcon
from PyQt6.QtCore import Qt

from src.config.settings import load_settings
from src.gui.main_window import MainWindow
from src.stt.whisper_models import is_model_cached, download_model


def _apply_dark_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base,            QColor(22, 22, 22))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button,          QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.BrightText,      Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link,            QColor(100, 160, 255))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(70, 130, 200))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def _resolve_icon() -> QIcon:
    from pathlib import Path
    if getattr(sys, "frozen", False):
        icon_path = Path(sys._MEIPASS) / "assets" / "RawriisIcon.png"
    else:
        icon_path = Path(__file__).parent / "assets" / "RawriisIcon.png"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("RawriisSTT")
    app.setOrganizationName("RawriisSTT")
    app.setWindowIcon(_resolve_icon())

    settings = load_settings()

    # Auto-download the base model on first run (silently in background before window opens)
    if settings.stt_engine == "whisper" and not is_model_cached("base"):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None,
            "Download Whisper Base Model",
            "The Whisper 'base' model (~145 MB) is not downloaded yet.\n\n"
            "Download it now? (Required for local speech recognition.)\n"
            "You can also choose a different STT engine in Settings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Downloading Whisper base model…", None, 0, 0)
            progress.setWindowTitle("Downloading")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.show()
            app.processEvents()
            try:
                download_model("base")
            except Exception as exc:
                QMessageBox.critical(None, "Download Failed", str(exc))
            finally:
                progress.close()

    if settings.dark_mode:
        _apply_dark_palette(app)
        app.setStyleSheet("""
            QToolTip { background: #2b2b2b; color: #dcdcdc; border: 1px solid #555; }
            QGroupBox { border: 1px solid #444; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #aaaaaa; }
            QPlainTextEdit { background: #1a1a1a; border: 1px solid #444; border-radius: 3px; }
            QComboBox { background: #2b2b2b; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; }
            QComboBox QAbstractItemView { background: #2b2b2b; selection-background-color: #3a5a8a; }
            QLineEdit { background: #1e1e1e; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; }
            QPushButton { background: #3a3a3a; border: 1px solid #555; border-radius: 4px; padding: 4px 12px; }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:pressed { background: #2a2a2a; }
            QPushButton:checked { background: #3a5a8a; border-color: #5a80b0; }
            QPushButton:disabled { background: #252525; color: #555555; border-color: #3a3a3a; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #2b2b2b; border: 1px solid #444; padding: 5px 14px; }
            QTabBar::tab:selected { background: #3a3a3a; border-bottom: none; }
            QCheckBox::indicator { border: 1px solid #555; border-radius: 2px; width: 13px; height: 13px; }
            QCheckBox::indicator:checked { background: #3a5a8a; border-color: #5a80b0; }
            QCheckBox:disabled { color: #666666; }
            QCheckBox::indicator:disabled { border-color: #3a3a3a; background: #252525; }
            QCheckBox::indicator:checked:disabled { background: #253040; border-color: #354050; }
            QSpinBox { background: #1e1e1e; border: 1px solid #555; border-radius: 3px; padding: 2px 4px; }
            QSpinBox:disabled { background: #161616; color: #555555; border-color: #3a3a3a; }
            QComboBox:disabled { background: #222222; color: #555555; border-color: #3a3a3a; }
        """)

    window = MainWindow(settings)
    window.show()

    exit_code = app.exec()
    # Force-exit so sounddevice/portaudio threads don't keep the process alive.
    import os
    os._exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.critical("Unhandled exception at top level:\n%s", traceback.format_exc())
        if _FROZEN:
            _log_file.flush()
        raise
