"""Interactive compilation dialog with live terminal output."""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QProgressBar, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from ...core.models import GameProject
from ...core.library import LibraryManager
from ...core.builder import BuildWorker
from ...core.launcher import GameLauncher


class CompileDialog(QDialog):
    launch_requested = pyqtSignal(str)  # game_id

    def __init__(self, project: GameProject, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.project = project
        self.library_mgr = library_mgr
        self.worker: Optional[BuildWorker] = None
        self.is_successful = False

        self.setWindowTitle(f"Kompilieren: {project.name}")
        self.resize(780, 520)
        self.setMinimumSize(600, 400)

        self._build_ui()
        self._start_compilation()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Info Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 10px; padding: 12px;")
        h_layout = QHBoxLayout(header_card)
        h_layout.setSpacing(14)

        icon_lbl = QLabel(self.project.icon_text)
        icon_lbl.setStyleSheet(f"""
            background-color: {self.project.color_accent}22;
            border: 1px solid {self.project.color_accent}55;
            border-radius: 8px;
            font-size: 24px;
        """)
        icon_lbl.setFixedSize(46, 46)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(icon_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)

        title_lbl = QLabel(f"Source-Build: <b>{self.project.name}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #f8fafc;")
        info_box.addWidget(title_lbl)

        self.step_lbl = QLabel("Vorbereitung...")
        self.step_lbl.setStyleSheet("font-size: 12px; color: #38bdf8; font-weight: bold;")
        info_box.addWidget(self.step_lbl)

        h_layout.addLayout(info_box, 1)

        open_src_btn = QPushButton("📁 Quellordner öffnen")
        open_src_btn.setProperty("class", "secondary-btn")
        src_path = os.path.expanduser(f"~/.local/share/recomp-center/sources/{self.project.id}")
        open_src_btn.clicked.connect(lambda: GameLauncher.open_game_folder(src_path))
        h_layout.addWidget(open_src_btn)

        layout.addWidget(header_card)

        # Live Console Output
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #060911;
                border: 1px solid #1e293b;
                border-radius: 8px;
                color: #e2e8f0;
                font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.console, 1)

        # Bottom Bar: Actions & Status
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.setProperty("class", "danger-btn")
        self.cancel_btn.clicked.connect(self._cancel_build)
        bottom_bar.addWidget(self.cancel_btn)

        bottom_bar.addStretch(1)

        self.play_btn = QPushButton("▶ Spiel jetzt starten")
        self.play_btn.setProperty("class", "success-btn")
        self.play_btn.setVisible(False)
        self.play_btn.clicked.connect(self._on_play_clicked)
        bottom_bar.addWidget(self.play_btn)

        self.close_btn = QPushButton("Schließen")
        self.close_btn.setProperty("class", "secondary-btn")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(self.close_btn)

        layout.addLayout(bottom_bar)

    def _start_compilation(self):
        self.worker = BuildWorker(self.project, self.library_mgr)
        self.worker.step_changed.connect(self._on_step_changed)
        self.worker.log_output.connect(self._append_log)
        self.worker.build_finished.connect(self._on_build_finished)
        self.worker.start()

    def _on_step_changed(self, step_name: str):
        self.step_lbl.setText(step_name)

    def _append_log(self, text: str):
        self.console.appendPlainText(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def _on_build_finished(self, success: bool, exe_path: str, message: str):
        self.is_successful = success
        self.cancel_btn.setVisible(False)
        self.close_btn.setEnabled(True)

        if success:
            self.step_lbl.setText("✅ Kompilierung erfolgreich abgeschlossen!")
            self.step_lbl.setStyleSheet("font-size: 12px; color: #10b981; font-weight: bold;")
            self.play_btn.setVisible(True)
            self._append_log("\n[FERTIG] Build erfolgreich! Das Spiel ist ab sofort startbereit.")
        else:
            self.step_lbl.setText("❌ Kompilierung fehlgeschlagen.")
            self.step_lbl.setStyleSheet("font-size: 12px; color: #ef4444; font-weight: bold;")
            self._append_log(f"\n[FEHLER] {message}")

    def _cancel_build(self):
        if self.worker:
            self.worker.cancel()
            self._append_log("\n[ABBRUCH] Vorgang wird beendet...")

    def _on_play_clicked(self):
        self.accept()
        self.launch_requested.emit(self.project.id)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Kompilierung abbrechen?",
                "Der Build-Prozess läuft noch. Möchtest du ihn wirklich abbrechen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
