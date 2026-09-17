"""Downloads and active installation progress view with modern styling."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal


class DownloadsView(QWidget):
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_item = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("Downloads & Installationen")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 0.3px;")
        title_box.addWidget(title)

        self.subtitle = QLabel("Aktive Downloads und Installationsverlauf.")
        self.subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(self.subtitle)
        layout.addLayout(title_box)

        # Active Download Card
        self.active_frame = QFrame()
        self.active_frame.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        active_layout = QVBoxLayout(self.active_frame)
        active_layout.setSpacing(12)

        active_title_row = QHBoxLayout()
        self.active_game_lbl = QLabel("Kein aktiver Download")
        self.active_game_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        active_title_row.addWidget(self.active_game_lbl, 1)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.setProperty("class", "danger-btn")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.cancel_btn.setVisible(False)
        active_title_row.addWidget(self.cancel_btn)
        active_layout.addLayout(active_title_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        active_layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Bereit")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        active_layout.addWidget(self.status_lbl)

        layout.addWidget(self.active_frame)

        # History Header Row
        hist_header = QHBoxLayout()
        hist_lbl = QLabel("Verlauf")
        hist_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
        hist_header.addWidget(hist_lbl)

        hist_header.addStretch(1)

        self.btn_clear_hist = QPushButton("Verlauf leeren")
        self.btn_clear_hist.setProperty("class", "secondary-btn")
        self.btn_clear_hist.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_hist.clicked.connect(self._clear_history)
        hist_header.addWidget(self.btn_clear_hist)

        layout.addLayout(hist_header)

        # History List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setSpacing(8)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.history_widget)

        layout.addWidget(scroll, 1)

    def set_active_download(self, game_name: str):
        self.active_game_lbl.setText(f"📥 {game_name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)
        self.status_lbl.setText("Initialisiere Download...")

    def update_progress(self, current: int, total: int, speed_str: str):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            curr_mb = current / (1024 * 1024)
            tot_mb = total / (1024 * 1024)
            self.status_lbl.setText(f"{curr_mb:.1f} MB / {tot_mb:.1f} MB ({percent}%) • {speed_str}")
        else:
            curr_mb = current / (1024 * 1024)
            self.status_lbl.setText(f"{curr_mb:.1f} MB geladen • {speed_str}")

    def update_status(self, msg: str):
        self.status_lbl.setText(msg)

    def mark_finished(self, game_name: str, success: bool, msg: str = ""):
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        if success:
            self.active_game_lbl.setText("Kein aktiver Download")
            self.status_lbl.setText("Letzte Installation erfolgreich abgeschlossen.")
        else:
            self.active_game_lbl.setText("Fehler bei der Installation")
            self.status_lbl.setText(msg or "Fehler aufgetreten.")

        # Add to history
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        r_layout = QHBoxLayout(row)
        icon = "✅" if success else "❌"
        lbl = QLabel(f"{icon} <b>{game_name}</b> — {msg or ('Erfolgreich installiert' if success else 'Fehlgeschlagen')}")
        lbl.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        r_layout.addWidget(lbl)
        self.history_layout.insertWidget(0, row)

    def _clear_history(self):
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

