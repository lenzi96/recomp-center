#!/usr/bin/env python3
"""
Recomp Center - Modern Graphical Installation & Setup Wizard.
Provides a multi-step setup experience:
- Welcome & System Prerequisites Audit
- Installation Paths & ROM Directory Configuration (with auto-detection)
- Live Installation Progress with Terminal Log
- Completion & Instant Launch
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Ensure parent directory is in sys.path
REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

INSTALLER_STYLESHEET = """
QWidget {
    background-color: transparent;
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", "Cantarell", "Noto Sans", sans-serif;
    font-size: 13px;
    outline: none;
}

QMainWindow {
    background-color: #0b0f19;
}

QFrame.wizard-card {
    background-color: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
}

QLineEdit {
    background-color: #0c1220;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}

QLineEdit:focus {
    border-color: #38bdf8;
    background-color: #0e172a;
}

QPushButton {
    background-color: #1e293b;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #27364f;
    border-color: #475569;
}

QPushButton:disabled {
    background-color: #0f172a;
    color: #64748b;
    border-color: #1e293b;
}

QPushButton.btn-primary {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid #38bdf8;
    font-weight: 700;
}

QPushButton.btn-primary:hover {
    background-color: #0369a1;
    border-color: #7dd3fc;
}

QProgressBar {
    border: 1px solid #1e293b;
    border-radius: 6px;
    background-color: #090d14;
    height: 16px;
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    color: #f8fafc;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 5px;
}

QCheckBox {
    spacing: 8px;
    font-size: 13px;
    color: #cbd5e1;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #334155;
    background-color: #0c1220;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}
"""


class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, games_dir: str, roms_dir: str, github_token: str, make_desktop_shortcut: bool):
        super().__init__()
        self.games_dir = games_dir
        self.roms_dir = roms_dir
        self.github_token = github_token
        self.make_desktop_shortcut = make_desktop_shortcut

    def run(self):
        try:
            home = Path.home()
            bin_dir = home / ".local" / "bin"
            app_dir = home / ".local" / "share" / "applications"
            share_base = home / ".local" / "share" / "recomp-center"
            app_install_dir = share_base / "app"
            hicolor_dir = home / ".local" / "share" / "icons" / "hicolor"
            pixmaps_dir = home / ".local" / "share" / "pixmaps"

            self.progress.emit(10, "Erstelle Zielverzeichnisse...")
            bin_dir.mkdir(parents=True, exist_ok=True)
            app_dir.mkdir(parents=True, exist_ok=True)
            share_base.mkdir(parents=True, exist_ok=True)
            app_install_dir.mkdir(parents=True, exist_ok=True)
            pixmaps_dir.mkdir(parents=True, exist_ok=True)
            if self.games_dir:
                Path(self.games_dir).mkdir(parents=True, exist_ok=True)
            time.sleep(0.2)

            self.progress.emit(25, "Kopiere Anwendungsdateien nach ~/.local/share/recomp-center/app...")
            dest_pkg = app_install_dir / "recomp_center"
            if dest_pkg.exists():
                shutil.rmtree(dest_pkg)
            shutil.copytree(REPO_DIR / "recomp_center", dest_pkg)

            # Copy top level files
            for fn in ["main.py", "recomp-center", "recomp-center.desktop", "recomp-center.png",
                       "CHANGELOG.md", "README.md", "setup.py", "pyproject.toml", "uninstall.sh"]:
                src = REPO_DIR / fn
                if src.exists():
                    shutil.copy(src, app_install_dir / fn)

            # Copy git folder if present so In-App updater can run git pull
            git_src = REPO_DIR / ".git"
            if git_src.is_dir():
                git_dest = app_install_dir / ".git"
                if git_dest.exists():
                    shutil.rmtree(git_dest)
                shutil.copytree(git_src, git_dest)
            time.sleep(0.2)

            self.progress.emit(50, "Installiere Standalone-Launcher nach ~/.local/bin/recomp-center...")
            dest_bin = bin_dir / "recomp-center"
            shutil.copy(REPO_DIR / "recomp-center", dest_bin)
            dest_bin.chmod(0o755)
            (app_install_dir / "main.py").chmod(0o755)
            (app_install_dir / "recomp-center").chmod(0o755)
            time.sleep(0.2)

            self.progress.emit(70, "Installiere Anwendungs-Icons...")
            icon_png = REPO_DIR / "recomp-center.png"
            if icon_png.exists():
                dest_128 = hicolor_dir / "128x128" / "apps"
                dest_128.mkdir(parents=True, exist_ok=True)
                shutil.copy(icon_png, dest_128 / "recomp-center.png")
                shutil.copy(icon_png, pixmaps_dir / "recomp-center.png")
            time.sleep(0.1)

            self.progress.emit(80, "Speichere Konfiguration (settings.json)...")
            cfg_file = share_base / "settings.json"
            cfg_data = {
                "games_dir": self.games_dir or str(share_base / "games"),
                "roms_dir": self.roms_dir or "",
                "github_token": self.github_token or "",
                "auto_check_updates": True,
                "create_desktop_shortcuts": self.make_desktop_shortcut,
            }
            if cfg_file.exists():
                try:
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        existing.update(cfg_data)
                        cfg_data = existing
                except Exception:
                    pass
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2)

            self.progress.emit(88, "Registriere Desktop-Menüeintrag...")
            desktop_file = app_dir / "recomp-center.desktop"
            shutil.copy(REPO_DIR / "recomp-center.desktop", desktop_file)
            desktop_file.chmod(0o644)

            if self.make_desktop_shortcut:
                for dt_candidate in [home / "Schreibtisch", home / "Desktop"]:
                    if dt_candidate.exists():
                        target_dt = dt_candidate / "recomp-center.desktop"
                        shutil.copy(REPO_DIR / "recomp-center.desktop", target_dt)
                        target_dt.chmod(0o755)
            time.sleep(0.2)

            self.progress.emit(95, "Aktualisiere Desktop- & Icon-Datenbanken...")
            if shutil.which("update-desktop-database"):
                subprocess.run(["update-desktop-database", str(app_dir)], check=False)
            if shutil.which("gtk-update-icon-cache"):
                subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(hicolor_dir)], check=False)

            self.progress.emit(100, "Installation erfolgreich abgeschlossen!")
            self.finished.emit(True, "Installation vollständig!")
        except Exception as e:
            self.finished.emit(False, str(e))


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recomp Center – Installations-Assistent")
        self.resize(720, 560)
        self.setFixedSize(720, 560)

        self.worker = None
        self.init_ui()
        self.setStyleSheet(INSTALLER_STYLESHEET)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(14)

        # -------------------------------------------------------------
        # Header Hero
        # -------------------------------------------------------------
        header = QFrame()
        header.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 10px; padding: 12px;")
        hl = QHBoxLayout(header)
        hl.setSpacing(14)

        icon_path = REPO_DIR / "recomp-center.png"
        icon_lbl = QLabel()
        if icon_path.exists():
            icon_lbl.setPixmap(QPixmap(str(icon_path)).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setText("⚡")
            icon_lbl.setStyleSheet("font-size: 32px; color: #38bdf8;")
        hl.addWidget(icon_lbl)

        htext = QVBoxLayout()
        htext.setSpacing(2)
        t_lbl = QLabel("Recomp Center")
        t_lbl.setStyleSheet("font-size: 19px; font-weight: 900; color: #f8fafc;")
        sub_lbl = QLabel("Grafischer Installations- und Einrichtungsassistent (v1.0.0)")
        sub_lbl.setStyleSheet("font-size: 12px; color: #38bdf8; font-weight: 600;")
        htext.addWidget(t_lbl)
        htext.addWidget(sub_lbl)
        hl.addLayout(htext, 1)

        cat_badge = QLabel("200 Projekte")
        cat_badge.setStyleSheet("background: #0284c7; color: #ffffff; font-weight: 700; padding: 5px 12px; border-radius: 6px; font-size: 11px;")
        hl.addWidget(cat_badge)

        root_layout.addWidget(header)

        # -------------------------------------------------------------
        # Pages Stack
        # -------------------------------------------------------------
        self.stack = QStackedWidget()

        # Page 0: Welcome & System Audit
        self.page_welcome = self._create_page_welcome()
        self.stack.addWidget(self.page_welcome)

        # Page 1: Options & Path Configuration
        self.page_options = self._create_page_options()
        self.stack.addWidget(self.page_options)

        # Page 2: Progress & Log
        self.page_progress = self._create_page_progress()
        self.stack.addWidget(self.page_progress)

        # Page 3: Complete
        self.page_complete = self._create_page_complete()
        self.stack.addWidget(self.page_complete)

        root_layout.addWidget(self.stack, 1)

        # -------------------------------------------------------------
        # Bottom Navigation Buttons
        # -------------------------------------------------------------
        self.btn_bar = QHBoxLayout()

        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.close)
        self.btn_bar.addWidget(btn_cancel)

        self.btn_bar.addStretch()

        self.btn_back = QPushButton("Zurück")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setEnabled(False)
        self.btn_bar.addWidget(self.btn_back)

        self.btn_next = QPushButton("Weiter")
        self.btn_next.setProperty("class", "btn-primary")
        self.btn_next.clicked.connect(self.go_next)
        self.btn_bar.addWidget(self.btn_next)

        root_layout.addLayout(self.btn_bar)

    def _create_page_welcome(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "wizard-card")
        cl = QVBoxLayout(card)
        cl.setSpacing(10)

        t = QLabel("Willkommen zur Installation des Recomp Centers!")
        t.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        cl.addWidget(t)

        desc = QLabel(
            "Das <b>Recomp Center</b> ist Ihr zentraler Desktop-Hub zum Entdecken, Herunterladen, Kompilieren "
            "und Starten von über <b>200 Video-Game Recompilation- und Decompilation-Projekten</b> auf Linux.<br><br>"
            "Inklusive <b>C-Speed Doctor V64 Byteswap-Konverter (4ms)</b>, lokalem Steam- & GOG-Asset-Import "
            "und <b>GitHub In-App Updater</b>."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.4;")
        cl.addWidget(desc)

        # System Checks
        cl.addSpacing(6)
        cl.addWidget(QLabel("<b>Systemvoraussetzungen & Komponenten-Check:</b>"))

        checks = [
            ("Python 3 & PyQt6 Runtime", True),
            ("C/C++ Compiler & Build-Tools (gcc, g++, make, git)", shutil.which("gcc") is not None and shutil.which("git") is not None),
            ("CMake & Ninja (für Decomp Source-Ports)", shutil.which("cmake") is not None and shutil.which("ninja") is not None),
            ("Archiv-Extraktoren (tar, gzip, unzip)", shutil.which("tar") is not None and shutil.which("unzip") is not None),
            ("Desktop- & XDG-Integration", shutil.which("update-desktop-database") is not None),
        ]

        for name, ok in checks:
            row = QHBoxLayout()
            icon = "✅" if ok else "⚠️"
            lbl_name = QLabel(f"{icon}  {name}")
            status = "Installiert & Bereit" if ok else "Optional für Decomps"
            color = "#10b981" if ok else "#ea580c"
            lbl_status = QLabel(status)
            lbl_status.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 11px;")
            row.addWidget(lbl_name)
            row.addStretch()
            row.addWidget(lbl_status)
            cl.addLayout(row)

        l.addWidget(card)
        l.addStretch()
        return w

    def _create_page_options(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "wizard-card")
        cl = QVBoxLayout(card)
        cl.setSpacing(10)

        t = QLabel("Pfade & Konfiguration")
        t.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        cl.addWidget(t)

        # 1. Games installation dir
        lbl_games = QLabel("📁 Spiele-Installationsverzeichnis:")
        lbl_games.setStyleSheet("font-weight: 600; font-size: 12px;")
        cl.addWidget(lbl_games)

        g_row = QHBoxLayout()
        default_games = str(Path.home() / ".local" / "share" / "recomp-center" / "games")
        self.in_games_dir = QLineEdit(default_games)
        g_row.addWidget(self.in_games_dir, 1)

        btn_browse_g = QPushButton("Durchsuchen...")
        btn_browse_g.clicked.connect(self._browse_games_dir)
        g_row.addWidget(btn_browse_g)
        cl.addLayout(g_row)

        # 2. ROMs Central directory
        lbl_roms = QLabel("🎮 Zentrales ROM-Verzeichnis (für automatischen 1-Klick ROM-Matcher):")
        lbl_roms.setStyleSheet("font-weight: 600; font-size: 12px;")
        cl.addWidget(lbl_roms)

        r_row = QHBoxLayout()
        detected_rom = self._detect_default_rom()
        self.in_roms_dir = QLineEdit(detected_rom)
        r_row.addWidget(self.in_roms_dir, 1)

        btn_browse_r = QPushButton("Durchsuchen...")
        btn_browse_r.clicked.connect(self._browse_roms_dir)
        r_row.addWidget(btn_browse_r)

        btn_auto_r = QPushButton("Auto-Erkennung")
        btn_auto_r.clicked.connect(self._auto_detect_rom)
        r_row.addWidget(btn_auto_r)
        cl.addLayout(r_row)

        # 3. Checkboxes
        cl.addSpacing(6)
        self.chk_shortcut = QCheckBox("Desktop-Verknüpfung auf dem Schreibtisch erstellen")
        self.chk_shortcut.setChecked(True)
        cl.addWidget(self.chk_shortcut)

        self.chk_menu = QCheckBox("Im Linux-Anwendungsmenü (XDG Applications) registrieren")
        self.chk_menu.setChecked(True)
        self.chk_menu.setEnabled(False)
        cl.addWidget(self.chk_menu)

        self.chk_bin = QCheckBox("Befehl 'recomp-center' in ~/.local/bin bereitstellen")
        self.chk_bin.setChecked(True)
        self.chk_bin.setEnabled(False)
        cl.addWidget(self.chk_bin)

        l.addWidget(card)
        l.addStretch()
        return w

    def _detect_default_rom(self) -> str:
        candidates = [
            "/run/media/julian/HDD/Downloads/N64/Games",
            "/run/media/julian/HDD/Downloads/N64",
            str(Path.home() / "ROMs"),
            str(Path.home() / "roms"),
            str(Path.home() / "Emulation" / "roms"),
            str(Path.home() / "Downloads"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return ""

    def _browse_games_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Spiele-Verzeichnis wählen", self.in_games_dir.text())
        if d:
            self.in_games_dir.setText(d)

    def _browse_roms_dir(self):
        d = QFileDialog.getExistingDirectory(self, "ROM-Verzeichnis wählen", self.in_roms_dir.text())
        if d:
            self.in_roms_dir.setText(d)

    def _auto_detect_rom(self):
        det = self._detect_default_rom()
        if det:
            self.in_roms_dir.setText(det)
            QMessageBox.information(self, "ROMs erkannt", f"ROM-Verzeichnis automatisch gefunden:\n{det}")
        else:
            QMessageBox.warning(self, "Nicht gefunden", "Kein typisches ROM-Verzeichnis automatisch erkannt.")

    def _create_page_progress(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "wizard-card")
        cl = QVBoxLayout(card)
        cl.setSpacing(12)

        t = QLabel("Installation wird durchgeführt...")
        t.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        cl.addWidget(t)

        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        cl.addWidget(self.pbar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("JetBrains Mono, monospace", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #090d14;
                border: 1px solid #1e293b;
                color: #cbd5e1;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        cl.addWidget(self.log_text, 1)

        l.addWidget(card)
        return w

    def _create_page_complete(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 0)
        l.setSpacing(12)

        card = QFrame()
        card.setProperty("class", "wizard-card")
        cl = QVBoxLayout(card)
        cl.setSpacing(14)

        t = QLabel("🎉 Installation erfolgreich abgeschlossen!")
        t.setStyleSheet("font-size: 17px; font-weight: 800; color: #38bdf8;")
        cl.addWidget(t)

        msg = QLabel(
            "Das <b>Recomp Center</b> wurde erfolgreich auf Ihrem System eingerichtet.<br><br>"
            "<b>Highlights:</b><br>"
            "• <b>200 Recomp- & Decomp-Titel</b> sofort startklar im Katalog<br>"
            "• <b>Doctor V64 Byteswap-Konverter (4ms)</b> einsatzbereit<br>"
            "• <b>GitHub In-App Updater</b> für automatische Release-Aktualisierungen aktiviert<br><br>"
            "Sie können die Anwendung jederzeit über das Anwendungsmenü oder mit dem Befehl <b>'recomp-center'</b> starten."
        )
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.5;")
        cl.addWidget(msg)

        cl.addSpacing(10)
        self.chk_launch = QCheckBox("Recomp Center jetzt direkt starten")
        self.chk_launch.setChecked(True)
        cl.addWidget(self.chk_launch)

        l.addWidget(card)
        l.addStretch()
        return w

    def go_next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self.stack.setCurrentIndex(1)
            self.btn_back.setEnabled(True)
            self.btn_next.setText("Jetzt installieren")
        elif idx == 1:
            self.stack.setCurrentIndex(2)
            self.btn_back.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.start_installation()
        elif idx == 3:
            if self.chk_launch.isChecked():
                bin_path = str(Path.home() / ".local" / "bin" / "recomp-center")
                subprocess.Popen([bin_path])
            self.close()

    def go_back(self):
        idx = self.stack.currentIndex()
        if idx == 1:
            self.stack.setCurrentIndex(0)
            self.btn_back.setEnabled(False)
            self.btn_next.setText("Weiter")

    def start_installation(self):
        from recomp_center.updater import get_github_token
        self.worker = InstallWorker(
            games_dir=self.in_games_dir.text().strip(),
            roms_dir=self.in_roms_dir.text().strip(),
            github_token=get_github_token() or "",
            make_desktop_shortcut=self.chk_shortcut.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.pbar.setValue(val)
        self.log_text.append(f"[{val}%] {msg}")

    def _on_finished(self, ok: bool, err: str):
        if ok:
            self.stack.setCurrentIndex(3)
            self.btn_next.setText("Fertigstellen")
            self.btn_next.setEnabled(True)
        else:
            QMessageBox.critical(self, "Installationsfehler", f"Fehler bei der Installation:\n{err}")
            self.btn_back.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Recomp Center Installer")
    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
