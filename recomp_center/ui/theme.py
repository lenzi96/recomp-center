"""
Theme and styling for Recomp Center.
Modern Dark-Slate palette with gaming-inspired accents.
"""

DARK_STYLESHEET = """
/* Global Application Styling */
QWidget {
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #0b0f19;
}

/* Sidebar styling */
QFrame#sidebar {
    background-color: #0c1220;
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
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QPushButton.nav-btn:checked {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    border-left: 3px solid #38bdf8;
}

/* Content Area */
QWidget#contentArea {
    background-color: #0b0f19;
}

/* Scroll Areas */
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0c1220;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Cards & Frames */
QFrame.game-card {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame.game-card:hover {
    border: 1px solid #38bdf8;
    background-color: #182238;
}

QFrame.detail-header {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 18px;
}

/* Inputs */
QLineEdit {
    background-color: #131b2e;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #0284c7;
}
QLineEdit:focus {
    border: 1px solid #38bdf8;
}

/* Buttons */
QPushButton.primary-btn {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton.primary-btn:hover {
    background-color: #0369a1;
}
QPushButton.primary-btn:pressed {
    background-color: #075985;
}

QPushButton.success-btn {
    background-color: #059669;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton.success-btn:hover {
    background-color: #047857;
}

QPushButton.secondary-btn {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton.secondary-btn:hover {
    background-color: #334155;
    color: #ffffff;
}

QPushButton.danger-btn {
    background-color: #7f1d1d;
    color: #fca5a5;
    border: 1px solid #991b1b;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton.danger-btn:hover {
    background-color: #991b1b;
    color: #ffffff;
}

/* Badges */
QLabel.badge {
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Progress bar */
QProgressBar {
    background-color: #1e293b;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    height: 16px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 6px;
}

/* Combo Box */
QComboBox {
    background-color: #131b2e;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
    color: #f8fafc;
}
QComboBox:focus {
    border-color: #38bdf8;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #131b2e;
    border: 1px solid #334155;
    selection-background-color: #0284c7;
    color: #f8fafc;
}
"""
