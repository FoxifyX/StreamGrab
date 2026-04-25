"""
StreamGrab - YouTube Downloader
Main entry point
"""

import sys
import os

# Ensure the app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QLinearGradient

from ui.main_window import MainWindow
from data.storage import Storage


def create_splash_pixmap() -> QPixmap:
    """Create a beautiful animated splash screen."""
    w, h = 500, 300
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Dark gradient background
    gradient = QLinearGradient(0, 0, w, h)
    gradient.setColorAt(0.0, QColor("#0A0A0F"))
    gradient.setColorAt(1.0, QColor("#12121A"))
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, w, h, 20, 20)

    # Accent glow
    glow = QLinearGradient(0, 0, w, h // 2)
    glow.setColorAt(0.0, QColor(99, 102, 241, 40))
    glow.setColorAt(1.0, QColor(99, 102, 241, 0))
    painter.setBrush(glow)
    painter.drawRoundedRect(0, 0, w, h // 2, 20, 20)

    # App name
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Arial", 36, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 80, w, 60, Qt.AlignCenter, "StreamGrab")

    # Tagline
    painter.setPen(QColor("#8B8FA8"))
    font2 = QFont("Arial", 12)
    painter.setFont(font2)
    painter.drawText(0, 145, w, 30, Qt.AlignCenter, "YouTube Downloader · Powered by yt-dlp")

    # Loading text
    painter.setPen(QColor("#6366F1"))
    font3 = QFont("Arial", 10)
    painter.setFont(font3)
    painter.drawText(0, 255, w, 25, Qt.AlignCenter, "Loading...")

    painter.end()
    return pixmap


def main():
    """Main application entry point."""
    # Enable High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("StreamGrab")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StreamGrab")

    # Initialize storage
    storage = Storage()
    storage.init_db()

    # Splash screen
    splash_pix = create_splash_pixmap()
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    splash.show()
    app.processEvents()

    # Load settings
    settings = storage.load_settings()

    # Create main window (hidden during splash)
    window = MainWindow(storage, settings)

    # Show after splash
    def show_main():
        splash.finish(window)
        window.show()
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(2000, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
