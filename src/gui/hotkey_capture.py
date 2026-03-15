from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class HotkeyCaptureDialog(QDialog):
    """Click-to-capture hotkey dialog (1-3 key combination)."""

    _MOD_ORDER = {"ctrl": 0, "shift": 1, "alt": 2, "win": 3}

    _QT_MAP: dict = {
        Qt.Key.Key_Control: "ctrl",
        Qt.Key.Key_Shift:   "shift",
        Qt.Key.Key_Alt:     "alt",
        Qt.Key.Key_Meta:    "win",
        Qt.Key.Key_Return:  "enter",
        Qt.Key.Key_Enter:   "enter",
        Qt.Key.Key_Space:   "space",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Tab:     "tab",
        Qt.Key.Key_Delete:  "delete",
        Qt.Key.Key_Insert:  "insert",
        Qt.Key.Key_Home:    "home",
        Qt.Key.Key_End:     "end",
        Qt.Key.Key_PageUp:  "page up",
        Qt.Key.Key_PageDown: "page down",
        Qt.Key.Key_Up:      "up",
        Qt.Key.Key_Down:    "down",
        Qt.Key.Key_Left:    "left",
        Qt.Key.Key_Right:   "right",
        Qt.Key.Key_F1:  "f1",  Qt.Key.Key_F2:  "f2",  Qt.Key.Key_F3:  "f3",
        Qt.Key.Key_F4:  "f4",  Qt.Key.Key_F5:  "f5",  Qt.Key.Key_F6:  "f6",
        Qt.Key.Key_F7:  "f7",  Qt.Key.Key_F8:  "f8",  Qt.Key.Key_F9:  "f9",
        Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
        Qt.Key.Key_Pause:      "pause",
        Qt.Key.Key_Print:      "print screen",
        Qt.Key.Key_ScrollLock: "scroll lock",
        Qt.Key.Key_NumLock:    "num lock",
        Qt.Key.Key_CapsLock:   "caps lock",
    }

    def __init__(self, current_key: str = "", title: str = "Set Hotkey", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(320, 150)

        self._pressed: set[str] = set()
        self._captured: str = current_key

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Press your key combination (1-3 keys):"))

        self._lbl_combo = QLabel(self.fmt(current_key) or "-")
        self._lbl_combo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_combo.setFrameShape(QFrame.Shape.StyledPanel)
        self._lbl_combo.setMinimumHeight(36)
        self._lbl_combo.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(self._lbl_combo)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        self._btn_ok = QPushButton("OK")
        self._btn_ok.setEnabled(bool(current_key))
        self._btn_ok.setDefault(True)
        self._btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self._btn_ok)
        layout.addLayout(btn_row)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    # ---------------------------------------------------------------- events

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        name = self._name(key)
        if not name:
            return
        if not self._pressed:
            self._captured = ""
            self._btn_ok.setEnabled(False)
            self._lbl_combo.setText("...")
        self._pressed.add(name)
        if len(self._pressed) <= 3:
            self._lbl_combo.setText(self.fmt(self._join(self._pressed)))

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        if not self._captured and self._pressed:
            keys = set(self._pressed)
            if 1 <= len(keys) <= 3:
                self._captured = self._join(keys)
                self._lbl_combo.setText(self.fmt(self._captured))
                self._btn_ok.setEnabled(True)
        name = self._name(event.key())
        if name:
            self._pressed.discard(name)

    # ---------------------------------------------------------------- result

    def captured_key(self) -> str:
        return self._captured

    # ---------------------------------------------------------------- helpers

    def _join(self, keys: set[str]) -> str:
        return "+".join(sorted(keys, key=lambda k: self._MOD_ORDER.get(k, 99)))

    @staticmethod
    def fmt(combo: str) -> str:
        """'ctrl+shift+r' -> 'Ctrl + Shift + R'"""
        if not combo:
            return ""
        return " + ".join(p.upper() if len(p) <= 3 else p.capitalize()
                          for p in combo.split("+"))

    @classmethod
    def _name(cls, qt_key: int) -> str:
        if qt_key in cls._QT_MAP:
            return cls._QT_MAP[qt_key]
        if 32 < qt_key < 127:
            return chr(qt_key).lower()
        return ""
