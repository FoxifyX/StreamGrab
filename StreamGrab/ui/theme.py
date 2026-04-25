"""
StreamGrab - Theme System
Material You / Google Pixel inspired design tokens and stylesheets.
"""

DARK_PALETTE = {
    "bg_primary": "#0D0D14",
    "bg_surface": "#16161F",
    "bg_elevated": "#1E1E2A",
    "bg_card": "#1A1A26",
    "bg_input": "#12121C",
    "accent": "#6366F1",
    "accent_hover": "#818CF8",
    "accent_pressed": "#4F52D4",
    "accent_subtle": "#6366F120",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "text_primary": "#F1F1F8",
    "text_secondary": "#8B8FA8",
    "text_disabled": "#4B4F66",
    "border": "#2A2A3A",
    "border_focus": "#6366F1",
    "divider": "#1F1F2C",
    "scrollbar": "#2A2A3A",
    "scrollbar_hover": "#6366F1",
}

LIGHT_PALETTE = {
    "bg_primary": "#F4F4FB",
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#F0F0F8",
    "bg_card": "#FAFAFF",
    "bg_input": "#EBEBF5",
    "accent": "#6366F1",
    "accent_hover": "#4F52D4",
    "accent_pressed": "#3B3DBF",
    "accent_subtle": "#6366F115",
    "success": "#059669",
    "warning": "#D97706",
    "error": "#DC2626",
    "text_primary": "#111827",
    "text_secondary": "#6B7280",
    "text_disabled": "#9CA3AF",
    "border": "#E5E7EB",
    "border_focus": "#6366F1",
    "divider": "#F3F4F6",
    "scrollbar": "#D1D5DB",
    "scrollbar_hover": "#6366F1",
}


def build_stylesheet(palette: dict) -> str:
    p = palette
    return f"""
/* ── Global ──────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {p['bg_primary']};
    color: {p['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    selection-background-color: {p['accent']};
    selection-color: white;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {p['bg_primary']};
}}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['scrollbar']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p['scrollbar_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {p['scrollbar']};
    border-radius: 3px;
}}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {p['text_primary']};
}}
QLabel#secondary {{
    color: {p['text_secondary']};
    font-size: 12px;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: 700;
    color: {p['text_primary']};
}}
QLabel#heading {{
    font-size: 15px;
    font-weight: 600;
    color: {p['text_primary']};
}}

/* ── URL Input ───────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {p['bg_input']};
    color: {p['text_primary']};
    border: 1.5px solid {p['border']};
    border-radius: 14px;
    padding: 12px 18px;
    font-size: 14px;
}}
QLineEdit:focus {{
    border-color: {p['border_focus']};
    background-color: {p['bg_elevated']};
}}
QLineEdit::placeholder {{
    color: {p['text_disabled']};
}}

/* ── ComboBox ────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {p['bg_elevated']};
    color: {p['text_primary']};
    border: 1.5px solid {p['border']};
    border-radius: 12px;
    padding: 8px 14px;
    font-size: 13px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {p['accent']};
}}
QComboBox:focus {{
    border-color: {p['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {p['text_secondary']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {p['bg_elevated']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: 4px;
    selection-background-color: {p['accent_subtle']};
    selection-color: {p['accent']};
}}

/* ── Progress Bar ────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {p['bg_elevated']};
    border: none;
    border-radius: 8px;
    height: 10px;
    text-align: center;
    font-size: 0px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent']}, stop:1 {p['accent_hover']});
    border-radius: 8px;
}}

/* ── Push Buttons ────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {p['bg_elevated']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {p['accent_subtle']};
    border-color: {p['accent']};
    color: {p['accent']};
}}
QPushButton:pressed {{
    background-color: {p['accent']};
    color: white;
}}
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent']}, stop:1 #818CF8);
    color: white;
    border: none;
    font-weight: 600;
    font-size: 14px;
    border-radius: 14px;
    padding: 13px 28px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent_hover']}, stop:1 #A5B4FC);
}}
QPushButton#primary:pressed {{
    background: {p['accent_pressed']};
}}
QPushButton#primary:disabled {{
    background: {p['bg_elevated']};
    color: {p['text_disabled']};
}}
QPushButton#danger {{
    background: transparent;
    color: {p['error']};
    border: 1px solid {p['error']}40;
    border-radius: 10px;
}}
QPushButton#danger:hover {{
    background: {p['error']}15;
    border-color: {p['error']};
}}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    padding: 6px;
    border-radius: 8px;
    color: {p['text_secondary']};
}}
QPushButton#icon_btn:hover {{
    background: {p['accent_subtle']};
    color: {p['accent']};
}}

/* ── Tabs ────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {p['text_secondary']};
    padding: 10px 20px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {p['accent']};
    border-bottom: 2px solid {p['accent']};
}}
QTabBar::tab:hover:!selected {{
    color: {p['text_primary']};
}}

/* ── CheckBox ────────────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 10px;
    color: {p['text_primary']};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1.5px solid {p['border']};
    background: {p['bg_elevated']};
}}
QCheckBox::indicator:checked {{
    background: {p['accent']};
    border-color: {p['accent']};
    image: none;
}}
QCheckBox::indicator:hover {{
    border-color: {p['accent']};
}}

/* ── List Widget ─────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {p['bg_surface']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    padding: 4px;
}}
QListWidget::item {{
    border-radius: 8px;
    padding: 6px;
    margin: 2px 0;
}}
QListWidget::item:selected {{
    background-color: {p['accent_subtle']};
    color: {p['accent']};
}}
QListWidget::item:hover:!selected {{
    background-color: {p['bg_elevated']};
}}

/* ── Tooltip ─────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {p['bg_elevated']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Group Box ───────────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {p['bg_card']};
    border: 1px solid {p['border']};
    border-radius: 14px;
    margin-top: 12px;
    padding: 16px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    color: {p['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Text Edit ───────────────────────────────────────────────────────── */
QTextEdit {{
    background-color: {p['bg_input']};
    color: {p['text_primary']};
    border: 1.5px solid {p['border']};
    border-radius: 12px;
    padding: 10px;
    font-size: 13px;
}}
QTextEdit:focus {{
    border-color: {p['accent']};
}}

/* ── Slider ──────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {p['bg_elevated']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p['accent']};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -7px 0;
}}
QSlider::sub-page:horizontal {{
    background: {p['accent']};
    border-radius: 2px;
}}

/* ── Separator ───────────────────────────────────────────────────────── */
QFrame[frameShape="4"] {{
    color: {p['divider']};
    background: {p['divider']};
    max-height: 1px;
    border: none;
}}

/* ── Status Bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background: {p['bg_surface']};
    color: {p['text_secondary']};
    font-size: 11px;
    border-top: 1px solid {p['border']};
    padding: 2px 10px;
}}

/* ── Menu ────────────────────────────────────────────────────────────── */
QMenu {{
    background: {p['bg_elevated']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 8px;
    color: {p['text_primary']};
}}
QMenu::item:selected {{
    background: {p['accent_subtle']};
    color: {p['accent']};
}}
QMenu::separator {{
    height: 1px;
    background: {p['border']};
    margin: 4px 12px;
}}
"""
