"""Settings view for Recomp Center."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from ...core.library import LibraryManager


class SettingsView(QWidget):
    def __init__(self, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.library_mgr = library_mgr
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("Einstellungen")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #f8fafc;")
        title_box.addWidget(title)

        subtitle = QLabel("Pfade, GitHub-API und Systemintegration verwalten.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        # Settings Card
        card = QFrame()
        card.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 12px; padding: 20px;")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        # 1. Games Directory
        dir_lbl = QLabel("📁 Spiele-Installationsverzeichnis:")
        dir_lbl.setStyleSheet("font-weight: 600; color: #f8fafc;")
        card_layout.addWidget(dir_lbl)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self.library_mgr.get_games_directory())
        dir_row.addWidget(self.dir_input, 1)

        browse_btn = QPushButton("Durchsuchen...")
        browse_btn.setProperty("class", "secondary-btn")
        browse_btn.clicked.connect(self._browse_games_dir)
        dir_row.addWidget(browse_btn)
        card_layout.addLayout(dir_row)

        # 2. Central ROMs Directory
        rom_lbl = QLabel("🎮 Zentrales ROM-Verzeichnis (für automatischen ROM-Abgleich):")
        rom_lbl.setStyleSheet("font-weight: 600; color: #f8fafc;")
        card_layout.addWidget(rom_lbl)

        rom_hint = QLabel("Wird vom automatischen 1-Klick ROM-Matcher durchsucht, um baseroms zu finden und zu konvertieren.")
        rom_hint.setStyleSheet("font-size: 11px; color: #94a3b8;")
        card_layout.addWidget(rom_hint)

        rom_row = QHBoxLayout()
        self.roms_dir_input = QLineEdit(self.library_mgr.get_roms_directory())
        rom_row.addWidget(self.roms_dir_input, 1)

        rom_browse_btn = QPushButton("Durchsuchen...")
        rom_browse_btn.setProperty("class", "secondary-btn")
        rom_browse_btn.clicked.connect(self._browse_roms_dir)
        rom_row.addWidget(rom_browse_btn)

        rom_auto_btn = QPushButton("Auto-Erkennung")
        rom_auto_btn.setProperty("class", "secondary-btn")
        rom_auto_btn.clicked.connect(self._auto_detect_rom_dir)
        rom_row.addWidget(rom_auto_btn)
        card_layout.addLayout(rom_row)

        # 3. GitHub Token
        token_lbl = QLabel("🔑 GitHub Personal Access Token (Optional):")
        token_lbl.setStyleSheet("font-weight: 600; color: #f8fafc;")
        card_layout.addWidget(token_lbl)

        token_hint = QLabel("Erhöht das GitHub API Limit von 60 auf 5.000 Anfragen/Stunde für schnelle Release-Prüfungen.")
        token_hint.setStyleSheet("font-size: 11px; color: #94a3b8;")
        card_layout.addWidget(token_hint)

        self.token_input = QLineEdit(self.library_mgr.get_github_token())
        self.token_input.setPlaceholderText("ghp_...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.token_input)

        # 3. Checkbox options
        self.desktop_cb = QCheckBox("Automatisch .desktop Verknüpfungen für installierte Spiele anlegen")
        self.desktop_cb.setChecked(self.library_mgr.settings.get("create_desktop_shortcuts", True))
        card_layout.addWidget(self.desktop_cb)

        # Save Button
        save_btn = QPushButton("Einstellungen speichern")
        save_btn.setProperty("class", "primary-btn")
        save_btn.setFixedWidth(180)
        save_btn.clicked.connect(self._save_settings)
        card_layout.addWidget(save_btn)

        layout.addWidget(card)

        # In-App Update & GitHub Center Card
        update_card = QFrame()
        update_card.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 12px; padding: 20px;")
        update_layout = QVBoxLayout(update_card)
        update_layout.setSpacing(12)

        up_title_row = QHBoxLayout()
        up_title = QLabel("🔄 App-Updates & GitHub-Anbindung")
        up_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        up_title_row.addWidget(up_title)
        up_title_row.addStretch()

        from ...updater import get_github_repo
        repo_badge = QLabel(f"Repo: {get_github_repo()}")
        repo_badge.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-size: 11px;")
        up_title_row.addWidget(repo_badge)
        update_layout.addLayout(up_title_row)

        up_desc = QLabel(
            "Das Recomp Center verfügt über ein integriertes GitHub-Update-Center (basierend auf der Cachy Security Suite Architektur). "
            "Es ermöglicht automatische Release-Prüfungen, 1-Klick-Upgrades via Git oder GitHub-Tarball, Build-Tools-Status und Changelog-Einsicht."
        )
        up_desc.setWordWrap(True)
        up_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        update_layout.addWidget(up_desc)

        up_btn_row = QHBoxLayout()
        btn_open_updater = QPushButton("🚀 Update- & System-Center öffnen...")
        btn_open_updater.setProperty("class", "primary-btn")
        btn_open_updater.clicked.connect(self._open_update_dialog)
        up_btn_row.addWidget(btn_open_updater)

        btn_cfg_repo = QPushButton("🔗 GitHub-Repository ändern...")
        btn_cfg_repo.setProperty("class", "secondary-btn")
        btn_cfg_repo.clicked.connect(self._configure_repo)
        up_btn_row.addWidget(btn_cfg_repo)
        up_btn_row.addStretch()
        update_layout.addLayout(up_btn_row)

        layout.addWidget(update_card)

        # About / Credits Card
        about_card = QFrame()
        about_card.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 12px; padding: 20px;")
        about_layout = QVBoxLayout(about_card)
        about_layout.setSpacing(8)

        about_title = QLabel("🎮 Über Recomp Center")
        about_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        about_layout.addWidget(about_title)

        about_desc = QLabel(
            "Recomp Center ist ein offener Hub zur Entdeckung und Verwaltung von "
            "Decompilation- und Static-Recompilation-Projekten auf Linux.<br><br>"
            "<b>Rechtlicher Hinweis:</b> Diese Anwendung lädt ausschließlich die quelloffenen Engine-Binaries "
            "und Port-Releases von GitHub herunter. Sämtliche urheberrechtlich geschützten Spieldaten (ROMs, ISOs, Musik) "
            "verbleiben in der Verantwortung des Nutzers und müssen aus rechtmäßig erworbenen Originalkopien bereitgestellt werden."
        )
        about_desc.setWordWrap(True)
        about_desc.setTextFormat(Qt.TextFormat.RichText)
        about_desc.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        about_layout.addWidget(about_desc)

        layout.addWidget(about_card)
        layout.addStretch(1)

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

