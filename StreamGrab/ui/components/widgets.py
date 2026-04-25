"""
StreamGrab - Reusable UI Components
Custom widgets with Material You animations and polish.
"""

import urllib.request
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QProgressBar, QHBoxLayout,
    QVBoxLayout, QFrame, QGraphicsOpacityEffect, QSizePolicy,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, Signal,
    QSize, QRect, QPoint, Property, QObject,
)
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QPainterPath, QLinearGradient,
    QFont, QMovie,
)


# ── Animated Progress Bar ─────────────────────────────────────────────────────

class AnimatedProgressBar(QProgressBar):
    """Progress bar with smooth animated fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(400)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_value_animated(self, value: int):
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(int(value))
        self._animation.start()


# ── Ripple Button ─────────────────────────────────────────────────────────────

class RippleButton(QPushButton):
    """Material-style button with ripple click effect."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._ripple_pos = QPoint(0, 0)
        self._ripple_radius = 0
        self._ripple_opacity = 0.0
        self._ripple_anim = None
        self._ripple_color = QColor(255, 255, 255, 60)

    def mousePressEvent(self, event):
        self._ripple_pos = event.pos()
        self._start_ripple()
        super().mousePressEvent(event)

    def _start_ripple(self):
        if self._ripple_anim:
            self._ripple_anim.stop()
        self._ripple_radius = 0
        self._ripple_opacity = 0.5
        self._ripple_anim = QTimer(self)
        self._ripple_anim.timeout.connect(self._animate_ripple)
        self._ripple_anim.start(16)

    def _animate_ripple(self):
        max_r = max(self.width(), self.height()) * 1.5
        self._ripple_radius += max_r / 15
        self._ripple_opacity -= 0.05
        if self._ripple_opacity <= 0 or self._ripple_radius >= max_r:
            if self._ripple_anim:
                self._ripple_anim.stop()
            self._ripple_opacity = 0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._ripple_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            color = QColor(self._ripple_color)
            color.setAlphaF(self._ripple_opacity)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                self._ripple_pos,
                int(self._ripple_radius),
                int(self._ripple_radius),
            )
            painter.end()


# ── Card Widget ───────────────────────────────────────────────────────────────

class Card(QFrame):
    """Rounded card container with subtle shadow."""

    def __init__(self, parent=None, padding: int = 16):
        super().__init__(parent)
        self.setObjectName("card")
        self.setContentsMargins(padding, padding, padding, padding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw shadow
        for i in range(4, 0, -1):
            shadow_color = QColor(0, 0, 0, 12 - i * 2)
            painter.setBrush(shadow_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                self.rect().adjusted(-i // 2, i, i // 2, i * 2),
                16, 16,
            )

        super().paintEvent(event)


# ── Thumbnail Label ───────────────────────────────────────────────────────────

class ThumbnailLabel(QLabel):
    """Displays a rounded thumbnail image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 90)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap: QPixmap | None = None
        self._show_placeholder()

    def _show_placeholder(self):
        px = QPixmap(160, 90)
        px.fill(QColor("#1A1A26"))
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#4B4F66"))
        f = QFont("Arial", 28)
        p.setFont(f)
        p.drawText(px.rect(), Qt.AlignCenter, "▶")
        p.end()
        self._pixmap = px
        self.update()

    def load_from_url(self, url: str):
        """Download and display thumbnail asynchronously."""
        import threading

        def _fetch():
            try:
                data = urllib.request.urlopen(url, timeout=5).read()
                px = QPixmap()
                px.loadFromData(data)
                if not px.isNull():
                    self._pixmap = px.scaled(
                        160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.update()
            except Exception:
                pass

        threading.Thread(target=_fetch, daemon=True).start()

    def paintEvent(self, event):
        if not self._pixmap:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.setClipPath(path)

        # Center-crop the pixmap
        pw, ph = self._pixmap.width(), self._pixmap.height()
        scale = max(self.width() / pw, self.height() / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        scaled = self._pixmap.scaled(nw, nh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()


# ── Info Badge ────────────────────────────────────────────────────────────────

class InfoBadge(QWidget):
    """Small colored pill-shaped badge."""

    def __init__(self, text: str, color: str = "#6366F1", parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(color)
        self.setFixedHeight(24)
        metrics = self.fontMetrics()
        self.setFixedWidth(metrics.horizontalAdvance(text) + 24)

    def setText(self, text: str):
        self._text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg = QColor(self._color)
        bg.setAlpha(30)
        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.setPen(self._color)
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)
        painter.end()


# ── Download Item Widget ──────────────────────────────────────────────────────

class DownloadItemWidget(QWidget):
    """
    A single row in the active downloads list.
    Shows thumbnail, title, progress bar, and stats.
    """
    cancel_requested = Signal(str)  # url

    def __init__(self, url: str, title: str = "Loading...", parent=None):
        super().__init__(parent)
        self.url = url
        self.setObjectName("downloadItem")
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Thumbnail
        self.thumb = ThumbnailLabel()
        layout.addWidget(self.thumb)

        # Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("heading")
        self.title_lbl.setWordWrap(False)
        font = self.title_lbl.font()
        font.setPointSize(12)
        font.setBold(True)
        self.title_lbl.setFont(font)
        info_col.addWidget(self.title_lbl)

        self.status_lbl = QLabel("Initializing...")
        self.status_lbl.setObjectName("secondary")
        info_col.addWidget(self.status_lbl)

        self.progress = AnimatedProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        info_col.addWidget(self.progress)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.speed_lbl = QLabel("─")
        self.speed_lbl.setObjectName("secondary")
        self.eta_lbl = QLabel("")
        self.eta_lbl.setObjectName("secondary")
        self.size_lbl = QLabel("")
        self.size_lbl.setObjectName("secondary")
        for lbl in (self.speed_lbl, self.eta_lbl, self.size_lbl):
            stats_row.addWidget(lbl)
        stats_row.addStretch()
        info_col.addLayout(stats_row)

        layout.addLayout(info_col, 1)

        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setObjectName("icon_btn")
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setToolTip("Cancel download")
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.url))
        layout.addWidget(self.cancel_btn)

    def update_progress(self, data: dict):
        status = data.get("status", "downloading")
        if status == "processing":
            self.status_lbl.setText("⚙ Processing / Converting...")
            self.progress.set_value_animated(100)
            return

        percent = data.get("percent", 0)
        speed = data.get("speed", "─")
        eta = data.get("eta", "─")
        size = data.get("size", "")
        downloaded = data.get("downloaded", "")

        self.progress.set_value_animated(int(percent))
        self.speed_lbl.setText(f"⚡ {speed}")
        self.eta_lbl.setText(f"⏱ {eta}" if eta != "─" else "")
        self.size_lbl.setText(f"📦 {downloaded} / {size}" if size else f"📦 {downloaded}")
        self.status_lbl.setText(f"Downloading... {percent:.1f}%")

    def set_title(self, title: str):
        self.title_lbl.setText(title[:80] + ("..." if len(title) > 80 else ""))

    def set_complete(self):
        self.progress.set_value_animated(100)
        self.status_lbl.setText("✓ Download complete")
        self.cancel_btn.setEnabled(False)

    def set_error(self, message: str):
        self.status_lbl.setText(f"✕ Error: {message[:60]}")
        self.progress.setValue(0)
        self.cancel_btn.setEnabled(False)


# ── History Item ──────────────────────────────────────────────────────────────

class HistoryItemWidget(QWidget):
    """One row in the download history list."""
    open_file = Signal(str)
    open_folder = Signal(str)
    delete_item = Signal(int)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.record = record
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Format badge
        fmt = (self.record.get("format") or "mp4").upper()
        color = "#10B981" if fmt == "MP3" else "#6366F1"
        badge = InfoBadge(fmt, color)
        layout.addWidget(badge)

        # Title + meta
        meta_col = QVBoxLayout()
        meta_col.setSpacing(2)

        title = self.record.get("title") or "Unknown"
        title_lbl = QLabel(title[:70] + ("..." if len(title) > 70 else ""))
        font = title_lbl.font()
        font.setPointSize(12)
        title_lbl.setFont(font)
        meta_col.addWidget(title_lbl)

        meta = QLabel(
            f"{self.record.get('quality','')} · {self.record.get('created_at','')[:16]}"
        )
        meta.setObjectName("secondary")
        meta_col.addWidget(meta)

        layout.addLayout(meta_col, 1)

        # Action buttons
        path = self.record.get("download_path") or ""
        if path:
            open_btn = QPushButton("📂")
            open_btn.setObjectName("icon_btn")
            open_btn.setFixedSize(32, 32)
            open_btn.setToolTip("Open folder")
            open_btn.clicked.connect(lambda: self.open_folder.emit(str(Path(path).parent)))
            layout.addWidget(open_btn)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("icon_btn")
        del_btn.setFixedSize(32, 32)
        del_btn.setToolTip("Remove from history")
        del_btn.clicked.connect(lambda: self.delete_item.emit(self.record.get("id", -1)))
        layout.addWidget(del_btn)


# ── Fade Widget ───────────────────────────────────────────────────────────────

class FadeWidget(QWidget):
    """Widget that can fade in/out."""

    def __init__(self, child: QWidget, parent=None):
        super().__init__(parent)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(child)

    def fade_in(self, duration: int = 300):
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

    def fade_out(self, duration: int = 200):
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.start()
        return anim
