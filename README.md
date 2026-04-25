# StreamGrab 🎬

**A beautiful, modern YouTube downloader with a Google Pixel / Material You interface.**

Built with Python, PySide6, and yt-dlp.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎥 Video Download | MP4 in 360p / 480p / 720p / 1080p / Best |
| 🎵 Audio Extraction | MP3 at 128 / 192 / 256 / 320 kbps via FFmpeg |
| 🎞 Playlist Download | Full playlist with one click |
| 📋 Batch Download | Paste multiple URLs, download all |
| 📷 Thumbnail Preview | See video thumbnail before downloading |
| 📊 Real-time Progress | Speed, ETA, file size, animated bar |
| 📂 Auto-organize | Separate Videos/ and Music/ folders |
| 🗂 Download History | SQLite-backed history with file management |
| 🌙 Dark / Light Mode | Smooth theme toggle |
| 📋 Clipboard Detection | Auto-pastes YouTube URLs |
| 🔔 System Notifications | Desktop tray notifications |
| 🖱 Drag & Drop | Drop YouTube URLs directly on the window |
| 🔁 Duplicate Detection | Warns before re-downloading |
| ⚡ Non-blocking UI | Downloads run in background threads |
| 💾 Persistent Settings | Remembers your preferences |

---

## 📋 Requirements

### Python
- Python 3.10 or higher

### Python Packages
```
PySide6>=6.6.0
yt-dlp>=2024.1.0
requests>=2.31.0
```

### FFmpeg (Required for MP3 conversion and merging)

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract and add the `bin/` folder to your system PATH
3. Or install via: `winget install ffmpeg` / `choco install ffmpeg`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

---

## 🚀 Installation & Running

### Step 1 — Clone or download the project
```bash
# If using git:
git clone https://github.com/FoxifyX/StreamGrab
cd StreamGrab

# Or just unzip and cd into the folder
```

### Step 2 — Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the app
```bash
python main.py
```

---

## 🗂 Project Structure

```
StreamGrab/
├── main.py                    # Entry point + splash screen
├── requirements.txt
├── README.md
│
├── ui/
│   ├── theme.py               # Color palettes + stylesheet
│   ├── main_window.py         # Main application window
│   └── components/
│       ├── widgets.py         # Reusable animated widgets
│       ├── settings_panel.py  # Settings tab
│       └── history_panel.py   # History tab
│
├── logic/
│   └── downloader.py          # yt-dlp wrappers + threading
│
├── services/
│   ├── file_manager.py        # File open/folder operations
│   └── notification_service.py # System tray + notifications
│
├── data/
│   └── storage.py             # SQLite DB + JSON settings
│
└── assets/
    ├── icons/
    └── thumbnails/
```

---

## 🎨 UI Guide

| Section | Description |
|---|---|
| ⬇ Download tab | Paste URL, fetch info, choose format/quality, download |
| ⚡ Active tab | Monitor all in-progress downloads with live stats |
| 📋 Batch tab | Multi-URL downloader |
| 📂 History tab | Past downloads with folder open & delete options |
| ⚙ Settings tab | Preferences, theme, directories, bitrates |
| 🌙 Sidebar moon | Toggle dark/light mode |

---

## 🔧 Troubleshooting

**"ffmpeg not found" error during MP3 download:**
- Install FFmpeg and ensure it's on your PATH (see above)

**"No module named PySide6":**
- Run `pip install PySide6`

**"No module named yt_dlp":**
- Run `pip install yt-dlp`

**Downloads are slow:**
- This is YouTube's server speed, not the app. yt-dlp uses the best available stream.

**Video info not loading:**
- Ensure the URL is a valid YouTube link (youtube.com/watch?v=... or youtu.be/...)

---

## 📝 Notes

- Downloads are saved to `~/Downloads/StreamGrab/` by default
- Settings and history are stored in `~/.streamgrab/`
- yt-dlp is kept updated automatically via pip; to update: `pip install -U yt-dlp`
- This app is for personal use. Please respect YouTube's Terms of Service.

---

## License

MIT — for personal / educational use.
