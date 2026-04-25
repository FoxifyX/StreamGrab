"""
StreamGrab - Downloader Logic
Wraps yt-dlp with progress callbacks, threading, and smart format selection.
"""

import os
import re
import threading
from pathlib import Path
from typing import Callable, Optional, Any

import yt_dlp


def clean_filename(name: str) -> str:
    """Remove characters invalid in filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]  # Limit length


def format_size(bytes_val: Optional[int]) -> str:
    if not bytes_val:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Unknown"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class DownloadWorker(threading.Thread):
    """
    Background thread for a single download task.
    Emits progress via callbacks (thread-safe via Qt signals wrapping).
    """

    def __init__(
        self,
        url: str,
        output_dir: str,
        format_type: str = "mp4",
        quality: str = "best",
        audio_bitrate: str = "192",
        embed_thumbnail: bool = True,
        organize_folders: bool = True,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_info: Optional[Callable] = None,
    ):
        super().__init__(daemon=True)
        self.url = url
        self.output_dir = output_dir
        self.format_type = format_type
        self.quality = quality
        self.audio_bitrate = audio_bitrate
        self.embed_thumbnail = embed_thumbnail
        self.organize_folders = organize_folders
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_info = on_info
        self._stop_event = threading.Event()
        self._downloaded_files: list[str] = []

    def stop(self):
        self._stop_event.set()

    def _get_output_template(self, is_audio: bool) -> str:
        if self.organize_folders:
            sub = "Music" if is_audio else "Videos"
            base = os.path.join(self.output_dir, sub)
        else:
            base = self.output_dir
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "%(title)s.%(ext)s")

    def _build_ydl_opts(self) -> dict:
        is_audio = self.format_type == "mp3"
        outtmpl = self._get_output_template(is_audio)

        # ── Format string ────────────────────────────────────────────────────
        if is_audio:
            fmt = "bestaudio/best"
        elif self.quality == "best":
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        elif self.quality == "1080p":
            fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"
        elif self.quality == "720p":
            fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"
        elif self.quality == "480p":
            fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"
        elif self.quality == "360p":
            fmt = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]"
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"

        opts: dict[str, Any] = {
            "format": fmt,
            "outtmpl": outtmpl,
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            "ignoreerrors": False,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }

        # ── Audio post-processing ─────────────────────────────────────────────
        if is_audio:
            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.audio_bitrate,
                }
            ]
            if self.embed_thumbnail:
                postprocessors.append({"key": "EmbedThumbnail"})
                opts["writethumbnail"] = True
            opts["postprocessors"] = postprocessors
        else:
            opts["merge_output_format"] = "mp4"

        return opts

    def _progress_hook(self, d: dict):
        if self._stop_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user")

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0)
            eta = d.get("eta", 0)

            percent = (downloaded / total * 100) if total else 0
            speed_str = f"{format_size(int(speed))}/s" if speed else "–"
            eta_str = f"{int(eta)}s" if eta else "–"
            size_str = format_size(total)

            if self.on_progress:
                self.on_progress(
                    {
                        "percent": percent,
                        "speed": speed_str,
                        "eta": eta_str,
                        "size": size_str,
                        "downloaded": format_size(downloaded),
                        "status": "downloading",
                    }
                )
        elif status == "finished":
            filename = d.get("filename", "")
            if filename:
                self._downloaded_files.append(filename)
            if self.on_progress:
                self.on_progress({"percent": 100, "status": "processing"})

    def run(self):
        try:
            opts = self._build_ydl_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

            if self.on_complete:
                title = info.get("title", "Unknown") if info else "Unknown"
                self.on_complete(
                    {
                        "url": self.url,
                        "title": title,
                        "format": self.format_type,
                        "quality": self.quality,
                        "files": self._downloaded_files,
                    }
                )
        except yt_dlp.utils.DownloadError as e:
            if "cancelled" not in str(e).lower():
                if self.on_error:
                    self.on_error(str(e))
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))


class InfoFetcher(threading.Thread):
    """Fetches video metadata without downloading."""

    def __init__(
        self,
        url: str,
        on_info: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        super().__init__(daemon=True)
        self.url = url
        self.on_info = on_info
        self.on_error = on_error

    def run(self):
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if self.on_info and info:
                formats = info.get("formats", [])
                # Collect unique heights
                heights = sorted(
                    set(
                        f.get("height", 0)
                        for f in formats
                        if f.get("height") and f.get("vcodec") != "none"
                    ),
                    reverse=True,
                )
                available_qualities = [f"{h}p" for h in heights if h] or ["best"]
                if "best" not in available_qualities:
                    available_qualities.insert(0, "best")

                self.on_info(
                    {
                        "title": info.get("title", "Unknown Title"),
                        "duration": format_duration(info.get("duration")),
                        "thumbnail": info.get("thumbnail", ""),
                        "uploader": info.get("uploader", "Unknown"),
                        "view_count": info.get("view_count", 0),
                        "available_qualities": available_qualities,
                        "is_playlist": info.get("_type") == "playlist",
                        "playlist_count": info.get("playlist_count", 0),
                        "description": (info.get("description") or "")[:200],
                    }
                )
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))


class PlaylistDownloader(threading.Thread):
    """Downloads an entire playlist with per-item progress."""

    def __init__(
        self,
        url: str,
        output_dir: str,
        format_type: str = "mp4",
        quality: str = "best",
        audio_bitrate: str = "192",
        organize_folders: bool = True,
        on_item_progress: Optional[Callable] = None,
        on_item_complete: Optional[Callable] = None,
        on_playlist_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        super().__init__(daemon=True)
        self.url = url
        self.output_dir = output_dir
        self.format_type = format_type
        self.quality = quality
        self.audio_bitrate = audio_bitrate
        self.organize_folders = organize_folders
        self.on_item_progress = on_item_progress
        self.on_item_complete = on_item_complete
        self.on_playlist_complete = on_playlist_complete
        self.on_error = on_error
        self._stop_event = threading.Event()
        self._current_index = 0
        self._total = 0

    def stop(self):
        self._stop_event.set()

    def _progress_hook(self, d: dict):
        if self._stop_event.is_set():
            raise yt_dlp.utils.DownloadError("cancelled")
        status = d.get("status")
        if status == "downloading" and self.on_item_progress:
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0)
            eta = d.get("eta", 0)
            percent = (downloaded / total * 100) if total else 0
            self.on_item_progress(
                {
                    "item_index": self._current_index,
                    "item_total": self._total,
                    "percent": percent,
                    "speed": f"{format_size(int(speed))}/s" if speed else "–",
                    "eta": f"{int(eta)}s" if eta else "–",
                }
            )

    def run(self):
        try:
            is_audio = self.format_type == "mp3"
            sub = "Music" if is_audio else "Videos"
            base = (
                os.path.join(self.output_dir, sub)
                if self.organize_folders
                else self.output_dir
            )
            os.makedirs(base, exist_ok=True)
            outtmpl = os.path.join(base, "%(playlist_index)s - %(title)s.%(ext)s")

            if is_audio:
                fmt = "bestaudio/best"
            elif self.quality == "best":
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
            else:
                h = self.quality.replace("p", "")
                fmt = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]"

            opts: dict[str, Any] = {
                "format": fmt,
                "outtmpl": outtmpl,
                "progress_hooks": [self._progress_hook],
                "ignoreerrors": True,
                "quiet": True,
                "no_warnings": True,
            }

            if is_audio:
                opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": self.audio_bitrate,
                    }
                ]

            completed = 0
            errors = 0

            with yt_dlp.YoutubeDL(opts) as ydl:
                # First, get playlist info
                info = ydl.extract_info(self.url, download=False)
                if info and info.get("_type") == "playlist":
                    entries = info.get("entries", [])
                    self._total = len([e for e in entries if e])
                else:
                    self._total = 1

                # Now download
                self._current_index = 0
                for entry in (info.get("entries", []) if info else []):
                    if self._stop_event.is_set():
                        break
                    if not entry:
                        continue
                    self._current_index += 1
                    try:
                        ydl.download([entry.get("webpage_url", entry.get("url", ""))])
                        completed += 1
                        if self.on_item_complete:
                            self.on_item_complete(
                                {
                                    "index": self._current_index,
                                    "total": self._total,
                                    "title": entry.get("title", "Unknown"),
                                }
                            )
                    except Exception:
                        errors += 1

            if self.on_playlist_complete:
                self.on_playlist_complete(
                    {"completed": completed, "errors": errors, "total": self._total}
                )

        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
