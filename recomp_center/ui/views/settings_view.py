"""Settings view for Recomp Center with scroll area and high-contrast styling."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QFrame, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt
from ...core.library import LibraryManager


class SettingsView(QWidget):
    def __init__(self, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.library_mgr = library_mgr
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area for entire settings page
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(22)
        scroll.setWidget(content)
        root_layout.addWidget(scroll)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Einstellungen")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: 0.3px;")
        title_box.addWidget(title)

        subtitle = QLabel("Pfade, Systemintegration, ROM-Erkennung und GitHub-Anbindung verwalten.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        # =============================================================
        # Card 1: Verzeichnisse & Speicherorte
        # =============================================================
        card_dirs = QFrame()
        card_dirs.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        c1_layout = QVBoxLayout(card_dirs)
        c1_layout.setSpacing(14)

        c1_title = QLabel("📁 Speicherorte & Pfade")
        c1_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        c1_layout.addWidget(c1_title)

        # 1. Games Directory
        dir_box = QVBoxLayout()
        dir_box.setSpacing(6)
        dir_lbl = QLabel("Spiele-Installationsverzeichnis:")
        dir_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9;")
        dir_box.addWidget(dir_lbl)

        dir_hint = QLabel("Ort, an dem heruntergeladene und kompilierte Ports entpackt und gespeichert werden.")
        dir_hint.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        dir_box.addWidget(dir_hint)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(8)
        self.dir_input = QLineEdit(self.library_mgr.get_games_directory())
        self.dir_input.setStyleSheet("font-size: 13px; padding: 9px 12px; color: #ffffff;")
        dir_row.addWidget(self.dir_input, 1)

        browse_btn = QPushButton("Ordner wählen...")
        browse_btn.setProperty("class", "secondary-btn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_games_dir)
        dir_row.addWidget(browse_btn)
        dir_box.addLayout(dir_row)
        c1_layout.addLayout(dir_box)

        # Separator line
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #1e293b;")
        c1_layout.addWidget(sep1)

        # 2. Central ROMs Directory
        rom_box = QVBoxLayout()
        rom_box.setSpacing(6)
        rom_lbl = QLabel("Zentrales ROM-Verzeichnis (für automatischen ROM-Abgleich):")
        rom_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9;")
        rom_box.addWidget(rom_lbl)

        rom_hint = QLabel("Wird vom 1-Klick ROM-Matcher automatisch durchsucht, um erforderliche Original-Dateien zuzuordnen.")
        rom_hint.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        rom_box.addWidget(rom_hint)

        rom_row = QHBoxLayout()
        rom_row.setSpacing(8)
        self.roms_dir_input = QLineEdit(self.library_mgr.get_roms_directory())
        self.roms_dir_input.setStyleSheet("font-size: 13px; padding: 9px 12px; color: #ffffff;")
        rom_row.addWidget(self.roms_dir_input, 1)

        rom_browse_btn = QPushButton("Ordner wählen...")
        rom_browse_btn.setProperty("class", "secondary-btn")
        rom_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rom_browse_btn.clicked.connect(self._browse_roms_dir)
        rom_row.addWidget(rom_browse_btn)

        rom_auto_btn = QPushButton("Auto-Erkennung")
        rom_auto_btn.setProperty("class", "secondary-btn")
        rom_auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rom_auto_btn.clicked.connect(self._auto_detect_rom_dir)
        rom_row.addWidget(rom_auto_btn)
        rom_box.addLayout(rom_row)
        c1_layout.addLayout(rom_box)

        layout.addWidget(card_dirs)

        # =============================================================
        # Card 2: Desktop & Systemintegration
        # =============================================================
        card_sys = QFrame()
        card_sys.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        c2_layout = QVBoxLayout(card_sys)
        c2_layout.setSpacing(12)

        c2_title = QLabel("🖥️ Desktop- & Systemintegration")
        c2_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        c2_layout.addWidget(c2_title)

        self.desktop_cb = QCheckBox("Automatisch Menü-Verknüpfung (.desktop) für jedes neu installierte Spiel anlegen")
        self.desktop_cb.setChecked(self.library_mgr.settings.get("create_desktop_shortcuts", True))
        self.desktop_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.desktop_cb.setStyleSheet("font-size: 13px; color: #f1f5f9; font-weight: 600;")
        c2_layout.addWidget(self.desktop_cb)

        cb_desc = QLabel("Ermöglicht das direkte Starten installierter Spiele aus dem Linux-Anwendungsmenü (GNOME, KDE, etc.).")
        cb_desc.setStyleSheet("font-size: 12px; color: #cbd5e1; padding-left: 28px;")
        c2_layout.addWidget(cb_desc)

        layout.addWidget(card_sys)

        # =============================================================
        # Card 3: GitHub API Authentifizierung
        # =============================================================
        card_gh = QFrame()
        card_gh.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        c3_layout = QVBoxLayout(card_gh)
        c3_layout.setSpacing(12)

        c3_title = QLabel("🔑 GitHub-Anbindung (Optional)")
        c3_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        c3_layout.addWidget(c3_title)

        token_lbl = QLabel("GitHub Personal Access Token:")
        token_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f1f5f9;")
        c3_layout.addWidget(token_lbl)

        token_hint = QLabel("Erhöht das GitHub API-Limit von 60 auf 5.000 Anfragen pro Stunde (hilft bei vielen gleichzeitigen Release-Prüfungen).")
        token_hint.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        c3_layout.addWidget(token_hint)

        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        self.token_input = QLineEdit(self.library_mgr.get_github_token())
        self.token_input.setPlaceholderText("ghp_...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet("font-size: 13px; padding: 9px 12px; color: #ffffff;")
        token_row.addWidget(self.token_input, 1)

        self.btn_toggle_token = QPushButton("Anzeigen")
        self.btn_toggle_token.setProperty("class", "secondary-btn")
        self.btn_toggle_token.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_token.clicked.connect(self._toggle_token_visibility)
        token_row.addWidget(self.btn_toggle_token)
        c3_layout.addLayout(token_row)

        layout.addWidget(card_gh)

        # =============================================================
        # Save Action Row
        # =============================================================
        save_box = QHBoxLayout()
        save_btn = QPushButton("💾 Einstellungen speichern")
        save_btn.setProperty("class", "primary-btn")
        save_btn.setMinimumWidth(220)
        save_btn.setMinimumHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        save_box.addWidget(save_btn)
        save_box.addStretch(1)
        layout.addLayout(save_box)

        # =============================================================
        # Card 4: In-App Updater Center
        # =============================================================
        card_up = QFrame()
        card_up.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        up_layout = QVBoxLayout(card_up)
        up_layout.setSpacing(12)

        up_title_row = QHBoxLayout()
        up_title = QLabel("🔄 Integriertes Update-Center")
        up_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        up_title_row.addWidget(up_title)
        up_title_row.addStretch()

        from ...updater import get_github_repo
        repo_badge = QLabel(f"Repo: {get_github_repo()}")
        repo_badge.setStyleSheet("background-color: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;")
        up_title_row.addWidget(repo_badge)
        up_layout.addLayout(up_title_row)

        up_desc = QLabel(
            "Das Recomp Center verfügt über ein integriertes GitHub-Update-Center (Cachy Security Suite Architektur). "
            "Es ermöglicht automatische Versionsprüfungen, 1-Klick-Upgrades via Git oder GitHub-Tarball, Build-Tools-Status und Changelog-Einsicht."
        )
        up_desc.setWordWrap(True)
        up_desc.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.5;")
        up_layout.addWidget(up_desc)

        up_btn_row = QHBoxLayout()
        up_btn_row.setSpacing(10)
        btn_open_updater = QPushButton("🚀 Update- & System-Center öffnen...")
        btn_open_updater.setProperty("class", "primary-btn")
        btn_open_updater.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_updater.clicked.connect(self._open_update_dialog)
        up_btn_row.addWidget(btn_open_updater)

        btn_cfg_repo = QPushButton("🔗 GitHub-Repository anpassen...")
        btn_cfg_repo.setProperty("class", "secondary-btn")
        btn_cfg_repo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cfg_repo.clicked.connect(self._configure_repo)
        up_btn_row.addWidget(btn_cfg_repo)
        up_btn_row.addStretch()
        up_layout.addLayout(up_btn_row)

        layout.addWidget(card_up)

        # =============================================================
        # Card 5: Über Recomp Center
        # =============================================================
        card_about = QFrame()
        card_about.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 18px;
            }
        """)
        about_layout = QVBoxLayout(card_about)
        about_layout.setSpacing(8)

        about_title = QLabel("ℹ️ Über Recomp Center & Rechtliche Hinweise")
        about_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        about_layout.addWidget(about_title)

        about_desc = QLabel(
            "Recomp Center ist ein offener Linux-Hub zur Entdeckung, Installation und Verwaltung von "
            "quelloffenen Decompilation- und Static-Recompilation-Projekten.<br><br>"
            "<b style='color: #fbbf24;'>Rechtlicher Hinweis:</b> Diese Anwendung lädt ausschließlich die frei verfügbaren, "
            "quelloffenen Engine-Binaries und Port-Releases von GitHub herunter. Sämtliche urheberrechtlich geschützten "
            "Spieldaten (ROMs, ISOs, Musik) verbleiben in der Verantwortung des Nutzers und müssen aus rechtmäßig erworbenen "
            "Originalkopien bereitgestellt werden."
        )
        about_desc.setWordWrap(True)
        about_desc.setTextFormat(Qt.TextFormat.RichText)
        about_desc.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.6;")
        about_layout.addWidget(about_desc)

        layout.addWidget(card_about)
        layout.addStretch(1)

    def _toggle_token_visibility(self):
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_token.setText("Verbergen")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_token.setText("Anzeigen")

    def _browse_games_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Spiele-Verzeichnis wählen", self.dir_input.text())
        if d:
            self.dir_input.setText(d)

    def _browse_roms_dir(self):
        d = QFileDialog.getExistingDirectory(self, "ROM-Verzeichnis wählen", self.roms_dir_input.text())
        if d:
            self.roms_dir_input.setText(d)

    def _auto_detect_rom_dir(self):
        from ...core.rom_scanner import RomAutoMatcher
        candidates = RomAutoMatcher.get_candidate_rom_dirs()
        if candidates:
            self.roms_dir_input.setText(candidates[0])
            QMessageBox.information(
                self,
                "ROM-Verzeichnis erkannt",
                f"Folgendes Verzeichnis wurde automatisch gefunden:\n{candidates[0]}"
            )
        else:
            QMessageBox.warning(self, "Kein Verzeichnis gefunden", "Es konnte kein typisches ROM-Verzeichnis automatisch erkannt werden.")

    def _save_settings(self):
        new_dir = self.dir_input.text().strip()
        if new_dir:
            self.library_mgr.set_games_directory(new_dir)

        rom_dir = self.roms_dir_input.text().strip()
        if rom_dir:
            self.library_mgr.set_roms_directory(rom_dir)

        self.library_mgr.set_github_token(self.token_input.text().strip())
        self.library_mgr.settings["create_desktop_shortcuts"] = self.desktop_cb.isChecked()
        self.library_mgr.save_settings()

        QMessageBox.information(self, "Gespeichert", "Einstellungen wurden erfolgreich übernommen!")

    def _open_update_dialog(self):
        from ...updater import UpdateDialog
        dlg = UpdateDialog(self)
        dlg.exec()

    def _configure_repo(self):
        from ...updater import UpdateDialog
        dlg = UpdateDialog(self)
        dlg.configure_github_repo()


