"""
StreamGrab - File Manager Service
Handles file operations: opening, organizing, and cleaning up.
"""

import os
import subprocess
import sys
from pathlib import Path


class FileManager:
    """Utility class for file operations."""

    @staticmethod
    def open_file(filepath: str):
        """Open a file with the system default application."""
        path = Path(filepath)
        if not path.exists():
            return False
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception as e:
            print(f"[FileManager] Cannot open file: {e}")
            return False

    @staticmethod
    def open_folder(folder_path: str):
        """Open a folder in the system file manager."""
        path = Path(folder_path)
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception as e:
            print(f"[FileManager] Cannot open folder: {e}")
            return False

    @staticmethod
    def ensure_dir(path: str) -> str:
        """Ensure a directory exists and return its path."""
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Return file size in bytes."""
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0

    @staticmethod
    def file_exists(filepath: str) -> bool:
        return Path(filepath).exists()
