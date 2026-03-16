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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.config.settings import load_settings
from src.gui.main_window import MainWindow
from src.gui.theme import apply_theme
from src.stt.whisper_models import is_model_cached, download_model


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

    apply_theme(app, settings.dark_mode)

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
