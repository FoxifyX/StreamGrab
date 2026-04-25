"""
StreamGrab - Data Storage
Handles SQLite database for history and JSON for settings.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_SETTINGS = {
    "theme": "dark",
    "download_dir": str(Path.home() / "Downloads" / "StreamGrab"),
    "default_format": "mp4",
    "default_quality": "best",
    "default_audio_bitrate": "192",
    "embed_thumbnail": True,
    "organize_folders": True,
    "clipboard_detect": True,
    "notifications": True,
    "sound_alert": False,
    "last_url": "",
}


class Storage:
    """Manages all persistent data for StreamGrab."""

    def __init__(self):
        self.app_dir = Path.home() / ".streamgrab"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.app_dir / "streamgrab.db"
        self.settings_path = self.app_dir / "settings.json"
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self):
        """Initialize database tables."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                filename TEXT,
                format TEXT,
                quality TEXT,
                file_size INTEGER,
                duration TEXT,
                download_path TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                thumbnail_url TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batch_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    # ── Settings ─────────────────────────────────────────────────────────────

    def load_settings(self) -> dict:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    saved = json.load(f)
                settings = DEFAULT_SETTINGS.copy()
                settings.update(saved)
                return settings
            except Exception:
                pass
        return DEFAULT_SETTINGS.copy()

    def save_settings(self, settings: dict):
        try:
            with open(self.settings_path, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"[Storage] Failed to save settings: {e}")

    # ── Download History ──────────────────────────────────────────────────────

    def add_download(self, data: dict) -> int:
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO downloads
               (url, title, filename, format, quality, file_size,
                duration, download_path, status, thumbnail_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("url", ""),
                data.get("title", ""),
                data.get("filename", ""),
                data.get("format", ""),
                data.get("quality", ""),
                data.get("file_size", 0),
                data.get("duration", ""),
                data.get("download_path", ""),
                data.get("status", "completed"),
                data.get("thumbnail_url", ""),
            ),
        )
        conn.commit()
        return cur.lastrowid

    def get_history(self, limit: int = 100) -> list:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cur.fetchall()]

    def is_duplicate(self, url: str) -> bool:
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT COUNT(*) FROM downloads WHERE url=? AND status='completed'", (url,)
        )
        return cur.fetchone()[0] > 0

    def clear_history(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads")
        conn.commit()

    def delete_download(self, download_id: int):
        conn = self._get_conn()
        conn.execute("DELETE FROM downloads WHERE id=?", (download_id,))
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
