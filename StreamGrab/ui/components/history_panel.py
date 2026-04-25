"""
StreamGrab - History Panel
Displays download history with file management actions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from ui.components.widgets import HistoryItemWidget
from services.file_manager import FileManager


class HistoryPanel(QWidget):
    """Download history list panel."""
    cleared = Signal()

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._items: list[HistoryItemWidget] = []
        self._setup_ui()
        self.reload()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Download History")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("secondary")
        header.addWidget(self.count_lbl)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear_all)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll)

        # Empty state
        self.empty_lbl = QLabel("No downloads yet.\nStart downloading to see your history here.")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setObjectName("secondary")
        self.empty_lbl.setStyleSheet("font-size: 14px; padding: 40px;")
        layout.addWidget(self.empty_lbl)

    def reload(self):
        """Reload history from database."""
        # Clear existing
        for item in self._items:
            item.deleteLater()
        self._items.clear()

        records = self.storage.get_history(limit=200)
        self.count_lbl.setText(f"{len(records)} downloads")

        if not records:
            self.empty_lbl.show()
            self.scroll.hide()
            return

        self.empty_lbl.hide()
        self.scroll.show()

        for record in records:
            item = HistoryItemWidget(record)
            item.open_file.connect(FileManager.open_file)
            item.open_folder.connect(FileManager.open_folder)
            item.delete_item.connect(self._delete_item)
            self._items.append(item)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

    def add_entry(self, record: dict):
        """Add a new entry to the top of the list."""
        self.empty_lbl.hide()
        self.scroll.show()

        item = HistoryItemWidget(record)
        item.open_file.connect(FileManager.open_file)
        item.open_folder.connect(FileManager.open_folder)
        item.delete_item.connect(self._delete_item)
        self._items.insert(0, item)
        self.list_layout.insertWidget(0, item)

        count = len(self._items)
        self.count_lbl.setText(f"{count} downloads")

    def _delete_item(self, download_id: int):
        if download_id < 0:
            return
        self.storage.delete_download(download_id)
        # Remove from UI
        for item in self._items[:]:
            if item.record.get("id") == download_id:
                item.deleteLater()
                self._items.remove(item)
                break
        self.count_lbl.setText(f"{len(self._items)} downloads")
        if not self._items:
            self.empty_lbl.show()
            self.scroll.hide()

    def _clear_all(self):
        self.storage.clear_history()
        for item in self._items:
            item.deleteLater()
        self._items.clear()
        self.count_lbl.setText("0 downloads")
        self.empty_lbl.show()
        self.scroll.hide()
        self.cleared.emit()
