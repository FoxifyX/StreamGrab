"""
StreamGrab - Notification Service
System tray icon and desktop notifications.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt


def _make_tray_icon() -> QIcon:
    """Create a simple tray icon programmatically."""
    px = QPixmap(32, 32)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#6366F1"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor("white"))
    painter.setFont(painter.font())
    painter.drawText(0, 0, 32, 32, Qt.AlignCenter, "▼")
    painter.end()
    return QIcon(px)


class NotificationService:
    """Manages system tray and desktop notifications."""

    def __init__(self, parent=None, on_show_window=None):
        self.tray = None
        self.on_show_window = on_show_window
        self._setup_tray(parent)

    def _setup_tray(self, parent):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray = QSystemTrayIcon(parent)
        self.tray.setIcon(_make_tray_icon())
        self.tray.setToolTip("StreamGrab - YouTube Downloader")

        # Context menu
        menu = QMenu()
        show_action = menu.addAction("Show StreamGrab")
        menu.addSeparator()
        quit_action = menu.addAction("Quit")

        if self.on_show_window:
            show_action.triggered.connect(self.on_show_window)

        from PySide6.QtWidgets import QApplication
        quit_action.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)

        if self.on_show_window:
            self.tray.activated.connect(self._on_tray_activated)

        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.on_show_window:
                self.on_show_window()

    def notify(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        if self.tray and self.tray.isSystemTrayAvailable():
            self.tray.showMessage(title, message, icon, 4000)

    def notify_complete(self, filename: str):
        self.notify("Download Complete ✓", f"{filename} downloaded successfully!")

    def notify_error(self, message: str):
        self.notify(
            "Download Failed",
            message,
            QSystemTrayIcon.Critical,
        )

    def hide(self):
        if self.tray:
            self.tray.hide()
