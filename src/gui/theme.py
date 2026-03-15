from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def apply_theme(app: QApplication, dark_mode: bool) -> None:
    if dark_mode:
        _apply_dark(app)
    else:
        _apply_pink(app)


def _apply_dark(app: QApplication) -> None:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(30, 30, 30))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base,            QColor(22, 22, 22))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(40, 40, 40))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(50, 50, 50))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Text,            QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button,          QColor(50, 50, 50))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.BrightText,      Qt.GlobalColor.red)
    p.setColor(QPalette.ColorRole.Link,            QColor(100, 160, 255))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(70, 130, 200))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(p)
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


def _apply_pink(app: QApplication) -> None:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(253, 240, 245))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(61, 32, 48))
    p.setColor(QPalette.ColorRole.Base,            QColor(255, 248, 251))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(249, 224, 236))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(252, 228, 236))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor(61, 32, 48))
    p.setColor(QPalette.ColorRole.Text,            QColor(61, 32, 48))
    p.setColor(QPalette.ColorRole.Button,          QColor(248, 187, 208))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(61, 32, 48))
    p.setColor(QPalette.ColorRole.BrightText,      QColor(194, 24, 91))
    p.setColor(QPalette.ColorRole.Link,            QColor(194, 24, 91))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(244, 143, 177))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(p)
    app.setStyleSheet("""
        QToolTip { background: #fce4ec; color: #3d2030; border: 1px solid #f48fb1; }
        QGroupBox { border: 1px solid #f48fb1; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #ad1457; }
        QPlainTextEdit { background: #fff8fb; border: 1px solid #f8bbd0; border-radius: 3px; }
        QComboBox { background: #fff8fb; border: 1px solid #f8bbd0; border-radius: 3px; padding: 2px 6px; }
        QComboBox QAbstractItemView { background: #fff8fb; selection-background-color: #f48fb1; }
        QLineEdit { background: #fff8fb; border: 1px solid #f8bbd0; border-radius: 3px; padding: 2px 6px; }
        QPushButton { background: #f8bbd0; border: 1px solid #f48fb1; border-radius: 4px; padding: 4px 12px; color: #3d2030; }
        QPushButton:hover { background: #fbc8da; }
        QPushButton:pressed { background: #f06292; color: #ffffff; }
        QPushButton:checked { background: #f06292; border-color: #ec407a; color: #ffffff; }
        QPushButton:disabled { background: #f8e8f0; color: #b09aa8; border-color: #f0c8d8; }
        QTabWidget::pane { border: 1px solid #f48fb1; }
        QTabBar::tab { background: #fce4ec; border: 1px solid #f48fb1; padding: 5px 14px; color: #3d2030; }
        QTabBar::tab:selected { background: #fff0f5; border-bottom: none; }
        QCheckBox::indicator { border: 1px solid #f48fb1; border-radius: 2px; width: 13px; height: 13px; background: #fff8fb; }
        QCheckBox::indicator:checked { background: #f06292; border-color: #ec407a; }
        QCheckBox:disabled { color: #c8a8b8; }
        QCheckBox::indicator:disabled { border-color: #f0c8d8; background: #f8e8f0; }
        QCheckBox::indicator:checked:disabled { background: #f8c8d8; border-color: #f0a8c0; }
        QSpinBox { background: #fff8fb; border: 1px solid #f8bbd0; border-radius: 3px; padding: 2px 4px; }
        QSpinBox:disabled { background: #f8e8f0; color: #b09aa8; border-color: #f0c8d8; }
        QComboBox:disabled { background: #f8e8f0; color: #b09aa8; border-color: #f0c8d8; }
    """)
