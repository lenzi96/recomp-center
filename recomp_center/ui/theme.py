"""
Theme and styling for Recomp Center.
Modern Dark-Slate & Midnight Gaming palette with polished accents.
"""

DARK_STYLESHEET = """
/* Global Application Styling */
QWidget {
    color: #f1f5f9;
    font-family: 'Inter', 'Segoe UI', 'Ubuntu', 'Noto Sans', -apple-system, sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #090d16;
}

/* Sidebar styling */
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0b0f19, stop:1 #0e1422);
    border-right: 1px solid #1e293b;
}

QFrame#sidebar QLabel {
    background: transparent;
    border: none;
}

/* Navigation Buttons */
QPushButton.nav-btn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 9px;
    text-align: left;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
}

QPushButton.nav-btn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    font-weight: 600;
    border: 1px solid #38bdf8;
}

/* Content Area */
QWidget#contentArea {
    background-color: #090d16;
}

/* Scroll Areas */
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Modern Minimal Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #090d16;
    width: 7px;
    margin: 0px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 28px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #090d16;
    height: 7px;
    margin: 0px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 28px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Game Cards & Containers */
QFrame.game-card {
    background-color: #111726;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame.game-card:hover {
    border: 1px solid #38bdf8;
    background-color: #151d30;
}

QFrame.detail-header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111827, stop:1 #172033);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px;
}

QFrame.glass-panel {
    background-color: #111726;
    border: 1px solid #1e293b;
    border-radius: 12px;
}

/* Inputs & Search */
QLineEdit {
    background-color: #111726;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 14px;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #0284c7;
}
QLineEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #151d30;
}

/* Primary Button */
QPushButton.primary-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
    color: #ffffff;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.primary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0284c7);
    border-color: #7dd3fc;
}
QPushButton.primary-btn:pressed {
    background-color: #075985;
}

/* Success Button */
QPushButton.success-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    border: 1px solid #34d399;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.success-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
    border-color: #6ee7b7;
}

/* Secondary Button */
QPushButton.secondary-btn {
    background-color: #1a2234;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 15px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton.secondary-btn:hover {
    background-color: #243048;
    color: #f8fafc;
    border-color: #475569;
}
QPushButton.secondary-btn:checked {
    background-color: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
    font-weight: 600;
}

/* Danger Button */
QPushButton.danger-btn {
    background-color: #451212;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 7px 15px;
    font-weight: 500;
}
QPushButton.danger-btn:hover {
    background-color: #7f1d1d;
    color: #ffffff;
    border-color: #991b1b;
}

/* Filter Chip / Pill */
QPushButton.pill-btn {
    background-color: #111726;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton.pill-btn:hover {
    background-color: #1a2234;
    color: #f1f5f9;
    border-color: #334155;
}
QPushButton.pill-btn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    border-color: #38bdf8;
}

/* Badges */
QLabel.badge {
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}

/* Progress bar */
QProgressBar {
    background-color: #111726;
    border: 1px solid #1e293b;
    border-radius: 7px;
    text-align: center;
    color: #f8fafc;
    height: 18px;
    font-weight: bold;
    font-size: 11px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 6px;
}

/* Combo Box */
QComboBox {
    background-color: #111726;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
    color: #f8fafc;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #475569;
}
QComboBox:focus {
    border-color: #38bdf8;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #111726;
    border: 1px solid #334155;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    color: #f8fafc;
    outline: none;
    padding: 4px;
}
"""
