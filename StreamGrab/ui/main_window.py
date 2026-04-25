"""
StreamGrab - Main Window
The full application UI: Google Pixel / Material You aesthetic.
"""

import os
import re
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTabWidget, QCheckBox,
    QFileDialog, QFrame, QScrollArea, QSizePolicy, QTextEdit,
    QProgressBar, QStatusBar, QMessageBox, QApplication,
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve,
    QThread, QObject, QSize, QRect,
)
from PySide6.QtGui import (
    QClipboard, QIcon, QPixmap, QColor, QPainter, QFont,
    QLinearGradient, QKeySequence, QShortcut,
)

from ui.theme import DARK_PALETTE, LIGHT_PALETTE, build_stylesheet
from ui.components.widgets import (
    AnimatedProgressBar, RippleButton, ThumbnailLabel,
    DownloadItemWidget, HistoryItemWidget, Card,
)
from ui.components.settings_panel import SettingsPanel
from ui.components.history_panel import HistoryPanel
from logic.downloader import DownloadWorker, InfoFetcher, PlaylistDownloader
from services.file_manager import FileManager
from services.notification_service import NotificationService
from data.storage import Storage


YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|playlist\?list=|shorts/)"
    r"|youtu\.be/)"
    r"[\w\-?=&%]+"
)


def is_youtube_url(text: str) -> bool:
    return bool(YOUTUBE_RE.search(text.strip()))


def make_icon_pixmap(emoji: str, size: int = 32, color: str = "#6366F1") -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(color))
    f = QFont()
    f.setPointSize(int(size * 0.55))
    p.setFont(f)
    p.drawText(QRect(0, 0, size, size), Qt.AlignCenter, emoji)
    p.end()
    return px


# ── Signal bridge (to safely update UI from worker threads) ──────────────────

class DownloadSignals(QObject):
    progress = Signal(str, dict)        # url, progress_data
    complete = Signal(str, dict)        # url, result_data
    error = Signal(str, str)            # url, message
    info_ready = Signal(dict)           # video info
    info_error = Signal(str)            # error message


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, storage: Storage, settings: dict):
        super().__init__()
        self.storage = storage
        self.settings = settings
        self._active_workers: dict[str, DownloadWorker | PlaylistDownloader] = {}
        self._active_items: dict[str, DownloadItemWidget] = {}
        self._info_fetcher: InfoFetcher | None = None
        self._current_info: dict = {}
        self._signals = DownloadSignals()

        self._setup_window()
        self._apply_theme()
        self._build_ui()
        self._connect_signals()
        self._setup_tray()
        self._start_clipboard_watcher()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("StreamGrab")
        self.setMinimumSize(800, 620)
        self.resize(980, 700)
        self.setWindowIcon(QIcon(make_icon_pixmap("▼", 64)))
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _apply_theme(self):
        palette = (
            DARK_PALETTE if self.settings.get("theme", "dark") == "dark"
            else LIGHT_PALETTE
        )
        self.setStyleSheet(build_stylesheet(palette))
        self._palette = palette

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        # Content area
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.tabBar().hide()  # we use custom sidebar nav
        root.addWidget(self.tab_widget, 1)

        # Build tabs
        self.tab_widget.addTab(self._build_download_tab(), "Download")
        self.tab_widget.addTab(self._build_active_tab(), "Active")
        self.tab_widget.addTab(self._build_batch_tab(), "Batch")
        self.tab_widget.addTab(self._build_history_tab(), "History")
        self.tab_widget.addTab(self._build_settings_tab(), "Settings")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — Paste a YouTube URL to get started")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(68)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(
            f"background-color: {self._palette['bg_surface']};"
            f"border-right: 1px solid {self._palette['border']};"
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        # App logo
        logo = QLabel("▼")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"color: {self._palette['accent']}; font-size: 24px; font-weight: bold; padding: 8px;")
        layout.addWidget(logo)
        layout.addSpacing(16)

        nav_items = [
            ("⬇", "Download", 0),
            ("⚡", "Active", 1),
            ("📋", "Batch", 2),
            ("📂", "History", 3),
            ("⚙", "Settings", 4),
        ]
        self._nav_buttons: list[QPushButton] = []
        for emoji, label, idx in nav_items:
            btn = QPushButton(emoji)
            btn.setFixedSize(52, 52)
            btn.setToolTip(label)
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._nav_click(i, b))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Theme toggle
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(52, 52)
        self.theme_btn.setToolTip("Toggle theme")
        self.theme_btn.setStyleSheet(self._nav_btn_style(False))
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Select first
        self._nav_buttons[0].setChecked(True)
        self._nav_buttons[0].setStyleSheet(self._nav_btn_style(True))

        return sidebar

    def _nav_btn_style(self, active: bool) -> str:
        p = self._palette
        if active:
            return (
                f"background: {p['accent_subtle']}; color: {p['accent']};"
                f"border: none; border-radius: 14px; font-size: 20px;"
            )
        return (
            f"background: transparent; color: {p['text_secondary']};"
            f"border: none; border-radius: 14px; font-size: 20px;"
        )

    def _nav_click(self, index: int, clicked_btn: QPushButton):
        self.tab_widget.setCurrentIndex(index)
        for btn in self._nav_buttons:
            btn.setChecked(btn is clicked_btn)
            btn.setStyleSheet(self._nav_btn_style(btn is clicked_btn))
        if index == 3:  # History tab
            self.history_panel.reload()

    # ── Download Tab ──────────────────────────────────────────────────────────

    def _build_download_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Title
        title_row = QHBoxLayout()
        title_lbl = QLabel("Download Video")
        title_lbl.setObjectName("title")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        open_folder_btn = QPushButton("📂 Open Folder")
        open_folder_btn.clicked.connect(self._open_downloads_folder)
        title_row.addWidget(open_folder_btn)
        layout.addLayout(title_row)

        # URL input card
        url_card = QFrame()
        url_card.setObjectName("card")
        url_card.setStyleSheet(
            f"background: {self._palette['bg_card']}; border-radius: 16px;"
            f"border: 1px solid {self._palette['border']};"
        )
        url_vlayout = QVBoxLayout(url_card)
        url_vlayout.setContentsMargins(16, 14, 16, 14)
        url_vlayout.setSpacing(10)

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🔗  Paste YouTube URL here…  (Ctrl+V)")
        self.url_input.setMinimumHeight(48)
        url_row.addWidget(self.url_input, 1)

        self.fetch_btn = RippleButton("Fetch Info")
        self.fetch_btn.setFixedHeight(48)
        self.fetch_btn.setMinimumWidth(110)
        self.fetch_btn.clicked.connect(self._fetch_info)
        url_row.addWidget(self.fetch_btn)

        self.paste_btn = QPushButton("📋")
        self.paste_btn.setObjectName("icon_btn")
        self.paste_btn.setFixedSize(48, 48)
        self.paste_btn.setToolTip("Paste from clipboard")
        self.paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(self.paste_btn)

        url_vlayout.addLayout(url_row)
        layout.addWidget(url_card)

        # Video info card (initially hidden)
        self.info_card = QFrame()
        self.info_card.setStyleSheet(
            f"background: {self._palette['bg_card']}; border-radius: 16px;"
            f"border: 1px solid {self._palette['border']};"
        )
        info_layout = QHBoxLayout(self.info_card)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(16)

        self.thumb_lbl = ThumbnailLabel()
        info_layout.addWidget(self.thumb_lbl)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(4)
        self.vid_title_lbl = QLabel("—")
        self.vid_title_lbl.setObjectName("heading")
        self.vid_title_lbl.setWordWrap(True)
        meta_col.addWidget(self.vid_title_lbl)

        self.vid_meta_lbl = QLabel("")
        self.vid_meta_lbl.setObjectName("secondary")
        meta_col.addWidget(self.vid_meta_lbl)

        self.vid_desc_lbl = QLabel("")
        self.vid_desc_lbl.setObjectName("secondary")
        self.vid_desc_lbl.setWordWrap(True)
        meta_col.addWidget(self.vid_desc_lbl)

        self.playlist_badge = QLabel("🎵 PLAYLIST")
        self.playlist_badge.setStyleSheet(
            f"color: {self._palette['accent']}; font-weight: 600; font-size: 11px;"
            f"background: {self._palette['accent_subtle']}; border-radius: 8px; padding: 2px 8px;"
        )
        self.playlist_badge.hide()
        meta_col.addWidget(self.playlist_badge)
        meta_col.addStretch()
        info_layout.addLayout(meta_col, 1)

        self.info_card.hide()
        layout.addWidget(self.info_card)

        # Options row
        opts_card = QFrame()
        opts_card.setStyleSheet(
            f"background: {self._palette['bg_card']}; border-radius: 16px;"
            f"border: 1px solid {self._palette['border']};"
        )
        opts_layout = QHBoxLayout(opts_card)
        opts_layout.setContentsMargins(16, 12, 16, 12)
        opts_layout.setSpacing(16)

        opts_layout.addWidget(QLabel("Format"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "webm", "mkv"])
        self.format_combo.setCurrentText(self.settings.get("default_format", "mp4"))
        self.format_combo.currentTextChanged.connect(self._on_format_change)
        opts_layout.addWidget(self.format_combo)

        opts_layout.addWidget(QLabel("Quality"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p"])
        self.quality_combo.setCurrentText(self.settings.get("default_quality", "best"))
        opts_layout.addWidget(self.quality_combo)

        opts_layout.addWidget(QLabel("Audio Bitrate"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128", "192", "256", "320"])
        self.bitrate_combo.setCurrentText(
            self.settings.get("default_audio_bitrate", "192")
        )
        opts_layout.addWidget(self.bitrate_combo)
        self.bitrate_combo.hide()
        self._bitrate_label = opts_layout.itemAt(opts_layout.count() - 2).widget() if False else None

        opts_layout.addStretch()

        self.playlist_toggle = QCheckBox("Playlist Mode")
        opts_layout.addWidget(self.playlist_toggle)

        layout.addWidget(opts_card)

        # Download button
        self.download_btn = RippleButton("⬇  Download")
        self.download_btn.setObjectName("primary")
        self.download_btn.setMinimumHeight(52)
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)

        # Inline progress (quick view)
        self.inline_progress_card = QFrame()
        self.inline_progress_card.setStyleSheet(
            f"background: {self._palette['bg_card']}; border-radius: 14px;"
            f"border: 1px solid {self._palette['border']};"
        )
        prog_layout = QVBoxLayout(self.inline_progress_card)
        prog_layout.setContentsMargins(16, 12, 16, 12)
        self.inline_status_lbl = QLabel("Preparing download...")
        self.inline_status_lbl.setObjectName("secondary")
        prog_layout.addWidget(self.inline_status_lbl)
        self.inline_progress = AnimatedProgressBar()
        self.inline_progress.setRange(0, 100)
        self.inline_progress.setFixedHeight(10)
        prog_layout.addWidget(self.inline_progress)
        self.inline_progress_card.hide()
        layout.addWidget(self.inline_progress_card)

        layout.addStretch()
        return tab

    # ── Active Downloads Tab ──────────────────────────────────────────────────

    def _build_active_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Active Downloads")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.active_count_lbl = QLabel("0 active")
        self.active_count_lbl.setObjectName("secondary")
        header.addWidget(self.active_count_lbl)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.active_container = QWidget()
        self.active_layout = QVBoxLayout(self.active_container)
        self.active_layout.setContentsMargins(0, 0, 0, 0)
        self.active_layout.setSpacing(8)
        self.active_layout.addStretch()

        scroll.setWidget(self.active_container)
        layout.addWidget(scroll)

        self.no_active_lbl = QLabel("No active downloads.\nStart a download to see it here.")
        self.no_active_lbl.setAlignment(Qt.AlignCenter)
        self.no_active_lbl.setObjectName("secondary")
        self.no_active_lbl.setStyleSheet("font-size: 14px; padding: 40px;")
        layout.addWidget(self.no_active_lbl)

        return tab

    # ── Batch Download Tab ────────────────────────────────────────────────────

    def _build_batch_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Batch Download")
        title.setObjectName("title")
        layout.addWidget(title)

        hint = QLabel("Enter one YouTube URL per line:")
        hint.setObjectName("secondary")
        layout.addWidget(hint)

        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\n..."
        )
        self.batch_input.setMinimumHeight(160)
        layout.addWidget(self.batch_input)

        # Batch options
        batch_opts = QHBoxLayout()
        batch_opts.addWidget(QLabel("Format"))
        self.batch_format = QComboBox()
        self.batch_format.addItems(["mp4", "mp3"])
        batch_opts.addWidget(self.batch_format)
        batch_opts.addWidget(QLabel("Quality"))
        self.batch_quality = QComboBox()
        self.batch_quality.addItems(["best", "1080p", "720p", "480p", "360p"])
        batch_opts.addWidget(self.batch_quality)
        batch_opts.addStretch()
        layout.addLayout(batch_opts)

        start_batch_btn = RippleButton("⬇  Download All")
        start_batch_btn.setObjectName("primary")
        start_batch_btn.setMinimumHeight(48)
        start_batch_btn.clicked.connect(self._start_batch)
        layout.addWidget(start_batch_btn)

        # Batch progress
        self.batch_progress_card = QFrame()
        self.batch_progress_card.setStyleSheet(
            f"background: {self._palette['bg_card']}; border-radius: 14px;"
            f"border: 1px solid {self._palette['border']};"
        )
        bpl = QVBoxLayout(self.batch_progress_card)
        bpl.setContentsMargins(16, 12, 16, 12)
        self.batch_status_lbl = QLabel("Starting batch...")
        self.batch_status_lbl.setObjectName("secondary")
        bpl.addWidget(self.batch_status_lbl)
        self.batch_progress = AnimatedProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setFixedHeight(10)
        bpl.addWidget(self.batch_progress)
        self.batch_progress_card.hide()
        layout.addWidget(self.batch_progress_card)

        layout.addStretch()
        return tab

    # ── History Tab ───────────────────────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        self.history_panel = HistoryPanel(self.storage)
        return self.history_panel

    # ── Settings Tab ─────────────────────────────────────────────────────────

    def _build_settings_tab(self) -> QWidget:
        self.settings_panel = SettingsPanel(self.settings)
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        return self.settings_panel

    # ── Signal connections ────────────────────────────────────────────────────

    def _connect_signals(self):
        self._signals.progress.connect(self._on_progress)
        self._signals.complete.connect(self._on_complete)
        self._signals.error.connect(self._on_error)
        self._signals.info_ready.connect(self._on_info_ready)
        self._signals.info_error.connect(self._on_info_error)

        # URL input
        self.url_input.returnPressed.connect(self._fetch_info)
        self.url_input.textChanged.connect(self._on_url_changed)

    # ── System Tray ───────────────────────────────────────────────────────────

    def _setup_tray(self):
        self.notifier = NotificationService(
            parent=self,
            on_show_window=self.show,
        )

    # ── Clipboard Watcher ─────────────────────────────────────────────────────

    def _start_clipboard_watcher(self):
        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.setInterval(1500)
        self._clipboard_timer.timeout.connect(self._check_clipboard)
        self._last_clipboard = ""
        if self.settings.get("clipboard_detect", True):
            self._clipboard_timer.start()

    def _check_clipboard(self):
        if not self.settings.get("clipboard_detect", True):
            return
        text = QApplication.clipboard().text().strip()
        if (
            text
            and text != self._last_clipboard
            and is_youtube_url(text)
            and not self.url_input.text().strip()
        ):
            self._last_clipboard = text
            self.url_input.setText(text)
            self.status_bar.showMessage("📋 YouTube URL auto-detected from clipboard")
            QTimer.singleShot(600, self._fetch_info)

    # ── Info Fetching ─────────────────────────────────────────────────────────

    def _on_url_changed(self, text: str):
        self.info_card.hide()
        self._current_info = {}
        self.playlist_toggle.setChecked(False)

    def _paste_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            self.status_bar.showMessage("📋 URL pasted from clipboard")

    def _fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return
        if not is_youtube_url(url):
            self.status_bar.showMessage("⚠ Please enter a valid YouTube URL")
            return

        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Fetching…")
        self.info_card.hide()
        self.status_bar.showMessage("🔍 Fetching video info...")

        fetcher = InfoFetcher(
            url=url,
            on_info=lambda info: self._signals.info_ready.emit(info),
            on_error=lambda e: self._signals.info_error.emit(e),
        )
        fetcher.start()

    def _on_info_ready(self, info: dict):
        self._current_info = info
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")

        self.vid_title_lbl.setText(info.get("title", "Unknown"))
        duration = info.get("duration", "")
        uploader = info.get("uploader", "")
        self.vid_meta_lbl.setText(f"👤 {uploader}  ·  ⏱ {duration}")
        desc = info.get("description", "")
        self.vid_desc_lbl.setText(desc[:120] + ("..." if len(desc) > 120 else "") if desc else "")

        # Thumbnail
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            self.thumb_lbl.load_from_url(thumb_url)

        # Playlist
        if info.get("is_playlist"):
            count = info.get("playlist_count", 0)
            self.playlist_badge.setText(f"🎵 PLAYLIST · {count} videos")
            self.playlist_badge.show()
            self.playlist_toggle.setChecked(True)
        else:
            self.playlist_badge.hide()
            self.playlist_toggle.setChecked(False)

        # Update quality options
        qualities = info.get("available_qualities", ["best", "1080p", "720p", "480p"])
        self.quality_combo.clear()
        self.quality_combo.addItems(qualities)

        self.info_card.show()
        self.status_bar.showMessage(f"✓ Info loaded: {info.get('title','')[:60]}")

    def _on_info_error(self, message: str):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Info")
        self.status_bar.showMessage(f"✕ Error: {message[:80]}")
        self.info_card.hide()

    def _on_format_change(self, fmt: str):
        is_audio = fmt == "mp3"
        self.quality_combo.setEnabled(not is_audio)

    # ── Download Orchestration ────────────────────────────────────────────────

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_bar.showMessage("⚠ Please enter a YouTube URL")
            return
        if not is_youtube_url(url):
            self.status_bar.showMessage("⚠ Invalid YouTube URL")
            return

        if url in self._active_workers:
            self.status_bar.showMessage("⚠ This URL is already downloading")
            return

        # Duplicate check
        if self.storage.is_duplicate(url):
            reply = QMessageBox.question(
                self,
                "Duplicate Download",
                "This URL has already been downloaded. Download again?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        fmt = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        bitrate = self.bitrate_combo.currentText()
        is_playlist = self.playlist_toggle.isChecked()
        output_dir = self.settings.get("download_dir", str(Path.home() / "Downloads" / "StreamGrab"))
        FileManager.ensure_dir(output_dir)

        title = self._current_info.get("title", "Video") if self._current_info else "Video"

        # Add to active downloads UI
        item = DownloadItemWidget(url, title)
        if self._current_info.get("thumbnail"):
            item.thumb.load_from_url(self._current_info["thumbnail"])
        item.cancel_requested.connect(self._cancel_download)

        self.active_layout.insertWidget(self.active_layout.count() - 1, item)
        self._active_items[url] = item
        self._update_active_count()
        self.no_active_lbl.hide()

        # Inline progress
        self.inline_progress_card.show()
        self.inline_progress.setValue(0)
        self.inline_status_lbl.setText(f"Downloading: {title[:50]}...")

        # Switch to active tab
        self._nav_click(1, self._nav_buttons[1])

        if is_playlist:
            worker = PlaylistDownloader(
                url=url,
                output_dir=output_dir,
                format_type=fmt,
                quality=quality,
                audio_bitrate=bitrate,
                organize_folders=self.settings.get("organize_folders", True),
                on_item_progress=lambda d: self._signals.progress.emit(url, d),
                on_item_complete=lambda d: self._on_playlist_item_done(url, d),
                on_playlist_complete=lambda d: self._signals.complete.emit(url, d),
                on_error=lambda e: self._signals.error.emit(url, e),
            )
        else:
            worker = DownloadWorker(
                url=url,
                output_dir=output_dir,
                format_type=fmt,
                quality=quality,
                audio_bitrate=bitrate,
                embed_thumbnail=self.settings.get("embed_thumbnail", True),
                organize_folders=self.settings.get("organize_folders", True),
                on_progress=lambda d: self._signals.progress.emit(url, d),
                on_complete=lambda d: self._signals.complete.emit(url, d),
                on_error=lambda e: self._signals.error.emit(url, e),
            )

        self._active_workers[url] = worker
        worker.start()
        self.status_bar.showMessage(f"⬇ Starting download: {title[:50]}...")

    def _cancel_download(self, url: str):
        worker = self._active_workers.get(url)
        if worker:
            worker.stop()
        self._remove_active(url)
        self.status_bar.showMessage("⏹ Download cancelled")

    # ── Download Events ───────────────────────────────────────────────────────

    def _on_progress(self, url: str, data: dict):
        item = self._active_items.get(url)
        if item:
            item.update_progress(data)
        # Update inline
        if "percent" in data:
            self.inline_progress.set_value_animated(int(data["percent"]))
            if data.get("status") == "processing":
                self.inline_status_lbl.setText("⚙ Processing...")
            else:
                pct = data.get("percent", 0)
                spd = data.get("speed", "─")
                eta = data.get("eta", "─")
                self.inline_status_lbl.setText(f"⬇ {pct:.1f}%  ·  {spd}  ·  ETA {eta}")

    def _on_complete(self, url: str, result: dict):
        item = self._active_items.get(url)
        if item:
            item.set_complete()

        title = result.get("title", "Download")
        files = result.get("files", [])

        # Save to history
        record = {
            "url": url,
            "title": title,
            "format": result.get("format", "mp4"),
            "quality": result.get("quality", "best"),
            "download_path": files[0] if files else "",
            "filename": files[0].split(os.sep)[-1] if files else "",
            "status": "completed",
        }
        row_id = self.storage.add_download(record)
        record["id"] = row_id

        self.history_panel.add_entry(record)

        # Notify
        if self.settings.get("notifications", True):
            self.notifier.notify_complete(title[:50])

        self.status_bar.showMessage(f"✓ Downloaded: {title[:60]}")
        self.inline_progress_card.hide()

        # Remove from active after delay
        QTimer.singleShot(3000, lambda: self._remove_active(url))

    def _on_playlist_item_done(self, playlist_url: str, data: dict):
        item = self._active_items.get(playlist_url)
        if item:
            idx = data.get("index", 0)
            total = data.get("total", 0)
            item.status_lbl.setText(f"✓ Item {idx}/{total}: {data.get('title','')[:40]}")

    def _on_error(self, url: str, message: str):
        item = self._active_items.get(url)
        if item:
            item.set_error(message)

        if self.settings.get("notifications", True):
            self.notifier.notify_error(message[:80])

        self.status_bar.showMessage(f"✕ Error: {message[:70]}")
        self.inline_progress_card.hide()
        self._active_workers.pop(url, None)

    def _remove_active(self, url: str):
        item = self._active_items.pop(url, None)
        if item:
            item.deleteLater()
        self._active_workers.pop(url, None)
        self._update_active_count()
        if not self._active_items:
            self.no_active_lbl.show()

    def _update_active_count(self):
        n = len(self._active_items)
        self.active_count_lbl.setText(f"{n} active")

    # ── Batch Download ────────────────────────────────────────────────────────

    def _start_batch(self):
        text = self.batch_input.toPlainText().strip()
        urls = [line.strip() for line in text.splitlines() if is_youtube_url(line.strip())]
        if not urls:
            self.status_bar.showMessage("⚠ No valid YouTube URLs found")
            return

        fmt = self.batch_format.currentText()
        quality = self.batch_quality.currentText()
        output_dir = self.settings.get("download_dir", str(Path.home() / "Downloads" / "StreamGrab"))
        FileManager.ensure_dir(output_dir)

        self.batch_progress_card.show()
        self.batch_progress.setValue(0)
        self.batch_status_lbl.setText(f"Starting {len(urls)} downloads...")

        for i, url in enumerate(urls):
            if url in self._active_workers:
                continue
            title = f"Batch #{i+1}"
            item = DownloadItemWidget(url, title)
            item.cancel_requested.connect(self._cancel_download)
            self.active_layout.insertWidget(self.active_layout.count() - 1, item)
            self._active_items[url] = item
            self.no_active_lbl.hide()

            worker = DownloadWorker(
                url=url,
                output_dir=output_dir,
                format_type=fmt,
                quality=quality,
                on_progress=lambda d, u=url: self._signals.progress.emit(u, d),
                on_complete=lambda d, u=url: self._signals.complete.emit(u, d),
                on_error=lambda e, u=url: self._signals.error.emit(u, e),
                organize_folders=self.settings.get("organize_folders", True),
            )
            self._active_workers[url] = worker
            worker.start()

        self._update_active_count()
        self._nav_click(1, self._nav_buttons[1])
        self.status_bar.showMessage(f"⬇ Started {len(urls)} batch downloads")

        # Batch progress animation
        self._batch_urls = urls[:]
        self._batch_timer = QTimer(self)
        self._batch_timer.timeout.connect(self._update_batch_progress)
        self._batch_timer.start(1000)

    def _update_batch_progress(self):
        total = len(self._batch_urls)
        done = sum(1 for u in self._batch_urls if u not in self._active_workers)
        if total > 0:
            self.batch_progress.set_value_animated(int(done / total * 100))
            self.batch_status_lbl.setText(f"Downloaded {done} / {total}")
        if done >= total:
            self._batch_timer.stop()
            self.batch_status_lbl.setText(f"✓ All {total} downloads complete!")

    # ── Settings & Theme ──────────────────────────────────────────────────────

    def _on_settings_changed(self, settings: dict):
        self.settings = settings
        self.storage.save_settings(settings)
        theme = settings.get("theme", "dark")
        palette = DARK_PALETTE if theme == "dark" else LIGHT_PALETTE
        self.setStyleSheet(build_stylesheet(palette))
        self._palette = palette
        clip = settings.get("clipboard_detect", True)
        if clip and not self._clipboard_timer.isActive():
            self._clipboard_timer.start()
        elif not clip:
            self._clipboard_timer.stop()

    def _toggle_theme(self):
        current = self.settings.get("theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self.settings["theme"] = new_theme
        self._on_settings_changed(self.settings)
        self.settings_panel.update_settings(self.settings)
        self.theme_btn.setText("☀" if new_theme == "light" else "🌙")

    # ── Folder Actions ────────────────────────────────────────────────────────

    def _open_downloads_folder(self):
        folder = self.settings.get("download_dir", str(Path.home() / "Downloads" / "StreamGrab"))
        FileManager.open_folder(folder)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if is_youtube_url(text):
                event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text().strip()
        if is_youtube_url(text):
            self.url_input.setText(text)
            self._nav_click(0, self._nav_buttons[0])
            QTimer.singleShot(200, self._fetch_info)

    # ── Window Events ─────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._active_workers:
            reply = QMessageBox.question(
                self,
                "Downloads in Progress",
                f"{len(self._active_workers)} download(s) in progress. Quit anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return

        # Stop workers
        for worker in self._active_workers.values():
            worker.stop()

        self.storage.save_settings(self.settings)
        self.notifier.hide()
        self.storage.close()
        event.accept()
