"""
StreamGrab - Settings Panel
User preferences and configuration UI.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QFileDialog, QGroupBox, QScrollArea,
    QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class SettingsPanel(QWidget):
    """Settings tab content."""
    settings_changed = Signal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # ── Download Location ─────────────────────────────────────────────
        dl_group = QGroupBox("DOWNLOAD LOCATION")
        dl_layout = QHBoxLayout(dl_group)

        self.dir_label = QLabel("~")
        self.dir_label.setObjectName("secondary")
        self.dir_label.setWordWrap(True)
        dl_layout.addWidget(self.dir_label, 1)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_dir)
        dl_layout.addWidget(browse_btn)

        main_layout.addWidget(dl_group)

        # ── Default Format ────────────────────────────────────────────────
        fmt_group = QGroupBox("DEFAULT FORMAT & QUALITY")
        fmt_layout = QHBoxLayout(fmt_group)

        fmt_layout.addWidget(QLabel("Format:"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["mp4", "mp3", "webm", "mkv"])
        self.fmt_combo.currentTextChanged.connect(self._on_change)
        fmt_layout.addWidget(self.fmt_combo)

        fmt_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p"])
        self.quality_combo.currentTextChanged.connect(self._on_change)
        fmt_layout.addWidget(self.quality_combo)

        fmt_layout.addStretch()
        main_layout.addWidget(fmt_group)

        # ── Audio Settings ─────────────────────────────────────────────────
        audio_group = QGroupBox("AUDIO SETTINGS")
        audio_layout = QHBoxLayout(audio_group)

        audio_layout.addWidget(QLabel("Default Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128", "192", "256", "320"])
        self.bitrate_combo.currentTextChanged.connect(self._on_change)
        audio_layout.addWidget(self.bitrate_combo)
        audio_layout.addWidget(QLabel("kbps"))
        audio_layout.addStretch()

        self.embed_thumb_chk = QCheckBox("Embed thumbnail in MP3 files")
        self.embed_thumb_chk.stateChanged.connect(self._on_change)
        audio_layout.addWidget(self.embed_thumb_chk)

        main_layout.addWidget(audio_group)

        # ── Organization ──────────────────────────────────────────────────
        org_group = QGroupBox("FILE ORGANIZATION")
        org_layout = QVBoxLayout(org_group)

        self.organize_chk = QCheckBox(
            "Auto-organize into Videos/ and Music/ subfolders"
        )
        self.organize_chk.stateChanged.connect(self._on_change)
        org_layout.addWidget(self.organize_chk)

        main_layout.addWidget(org_group)

        # ── UX Preferences ────────────────────────────────────────────────
        ux_group = QGroupBox("APP BEHAVIOR")
        ux_layout = QVBoxLayout(ux_group)

        self.clipboard_chk = QCheckBox("Auto-detect YouTube URLs from clipboard")
        self.clipboard_chk.stateChanged.connect(self._on_change)
        ux_layout.addWidget(self.clipboard_chk)

        self.notif_chk = QCheckBox("Show desktop notification on download complete")
        self.notif_chk.stateChanged.connect(self._on_change)
        ux_layout.addWidget(self.notif_chk)

        self.sound_chk = QCheckBox("Play sound alert on download complete")
        self.sound_chk.stateChanged.connect(self._on_change)
        ux_layout.addWidget(self.sound_chk)

        main_layout.addWidget(ux_group)

        # ── Theme ──────────────────────────────────────────────────────────
        theme_group = QGroupBox("APPEARANCE")
        theme_layout = QHBoxLayout(theme_group)
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        main_layout.addWidget(theme_group)

        main_layout.addStretch()

    def _load_values(self):
        s = self.settings
        self.dir_label.setText(s.get("download_dir", "~/Downloads/StreamGrab"))

        idx = self.fmt_combo.findText(s.get("default_format", "mp4"))
        self.fmt_combo.setCurrentIndex(max(0, idx))

        idx = self.quality_combo.findText(s.get("default_quality", "best"))
        self.quality_combo.setCurrentIndex(max(0, idx))

        idx = self.bitrate_combo.findText(s.get("default_audio_bitrate", "192"))
        self.bitrate_combo.setCurrentIndex(max(0, idx))

        self.embed_thumb_chk.setChecked(s.get("embed_thumbnail", True))
        self.organize_chk.setChecked(s.get("organize_folders", True))
        self.clipboard_chk.setChecked(s.get("clipboard_detect", True))
        self.notif_chk.setChecked(s.get("notifications", True))
        self.sound_chk.setChecked(s.get("sound_alert", False))

        idx = self.theme_combo.findText(s.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(max(0, idx))

    def _browse_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Download Directory",
            self.settings.get("download_dir", str(Path.home() / "Downloads")),
        )
        if folder:
            self.settings["download_dir"] = folder
            self.dir_label.setText(folder)
            self.settings_changed.emit(self.settings)

    def _on_change(self):
        self.settings["default_format"] = self.fmt_combo.currentText()
        self.settings["default_quality"] = self.quality_combo.currentText()
        self.settings["default_audio_bitrate"] = self.bitrate_combo.currentText()
        self.settings["embed_thumbnail"] = self.embed_thumb_chk.isChecked()
        self.settings["organize_folders"] = self.organize_chk.isChecked()
        self.settings["clipboard_detect"] = self.clipboard_chk.isChecked()
        self.settings["notifications"] = self.notif_chk.isChecked()
        self.settings["sound_alert"] = self.sound_chk.isChecked()
        self.settings_changed.emit(self.settings)

    def _on_theme_change(self):
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings_changed.emit(self.settings)

    def update_settings(self, settings: dict):
        self.settings = settings.copy()
        self._load_values()
