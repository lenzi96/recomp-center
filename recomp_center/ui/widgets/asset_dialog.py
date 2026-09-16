"""Interactive dialog for managing, importing and downloading required game assets and ROMs."""

import os
import shutil
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QFrame, QLineEdit, QProgressBar,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

from ...core.models import GameProject, InstalledGame
from ...core.library import LibraryManager
from ...core.launcher import GameLauncher
from ...core.asset_downloader import (
    FREE_ASSET_PACKS, SteamGOGScanner, AssetDownloadWorker
)
from ...core.rom_scanner import RomAutoMatcher, ROM_MATCH_RULES


class AssetDialog(QDialog):
    def __init__(self, project: GameProject, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.project = project
        self.library_mgr = library_mgr
        self.installed = library_mgr.get_installed(project.id)
        self.active_worker: Optional[AssetDownloadWorker] = None

        self.setWindowTitle(f"Spieldateien & ROMs: {project.name}")
        self.resize(650, 560)
        self.setMinimumSize(540, 480)
        self._build_ui()

    def _get_target_dir(self) -> str:
        """Returns destination directory: either installed game dir or sources dir."""
        if self.installed:
            return self.installed.install_path
        # Default fallback
        base_dir = os.path.expanduser("~/.local/share/recomp-center")
        p = os.path.join(base_dir, "games", self.project.id)
        os.makedirs(p, exist_ok=True)
        return p

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        # Title
        title_box = QHBoxLayout()
        title_icon = QLabel(self.project.icon_text)
        title_icon.setStyleSheet("font-size: 26px;")
        title_box.addWidget(title_icon)

        title = QLabel(f"Spieldateien-Manager: <b>{self.project.name}</b>")
        title.setStyleSheet("font-size: 17px; color: #f8fafc;")
        title_box.addWidget(title, 1)
        root_layout.addLayout(title_box)

        # Scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        # -------------------------------------------------------------
        # Section 1: Checklist of Required Files
        # -------------------------------------------------------------
        self.files_box = QFrame()
        self.files_box.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 10px; padding: 12px;")
        self.files_layout = QVBoxLayout(self.files_box)
        layout.addWidget(self.files_box)

        # -------------------------------------------------------------
        # Section 2: Option A - Free/Demo/Shareware 1-Click Download
        # -------------------------------------------------------------
        if self.project.id in FREE_ASSET_PACKS:
            pack = FREE_ASSET_PACKS[self.project.id]
            free_card = QFrame()
            free_card.setStyleSheet("background-color: #064e3b; border: 1px solid #059669; border-radius: 10px; padding: 14px;")
            f_layout = QVBoxLayout(free_card)
            f_layout.setSpacing(8)

            f_title = QLabel(f"🎁 Kostenlose Spieldaten verfügbar: {pack['title']}")
            f_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #6ee7b7;")
            f_layout.addWidget(f_title)

            f_desc = QLabel(pack["desc"])
            f_desc.setStyleSheet("font-size: 12px; color: #d1fae5;")
            f_desc.setWordWrap(True)
            f_layout.addWidget(f_desc)

            dl_btn = QPushButton("⬇ Kostenlose Spieldaten herunterladen & einrichten")
            dl_btn.setProperty("class", "success-btn")
            dl_btn.clicked.connect(lambda: self._start_asset_download(pack["url"], pack["filename"]))
            f_layout.addWidget(dl_btn)

            layout.addWidget(free_card)

        # -------------------------------------------------------------
        # Section 3: Option B - Local Steam & GOG Auto-Detection
        # -------------------------------------------------------------
        steam_res = SteamGOGScanner.scan_for_game(self.project.id)
        if steam_res:
            steam_card = QFrame()
            steam_card.setStyleSheet("background-color: #1e1b4b; border: 1px solid #4338ca; border-radius: 10px; padding: 14px;")
            s_layout = QVBoxLayout(steam_card)
            s_layout.setSpacing(8)

            s_title = QLabel("🎮 In deiner lokalen Steam/GOG-Bibliothek gefunden!")
            s_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #a5b4fc;")
            s_layout.addWidget(s_title)

            s_path = QLabel(f"Pfad: <span style='color:#38bdf8;'>{steam_res['game_dir']}</span>")
            s_path.setTextFormat(Qt.TextFormat.RichText)
            s_path.setStyleSheet("font-size: 11px; color: #cbd5e1;")
            s_layout.addWidget(s_path)

            import_steam_btn = QPushButton("⚡ 1-Klick Import aus Steam/GOG")
            import_steam_btn.setProperty("class", "primary-btn")
            import_steam_btn.clicked.connect(lambda: self._import_from_steam(steam_res["game_dir"]))
            s_layout.addWidget(import_steam_btn)

            layout.addWidget(steam_card)

        # -------------------------------------------------------------
        # Section 4: Option C - Automatischer ROM-Abgleich (Auto-Scanner & Konverter)
        # -------------------------------------------------------------
        is_rom_game = (
            self.project.id in ROM_MATCH_RULES or
            any(f.lower().endswith((".z64", ".n64", ".v64", ".gba", ".gb", ".bin", ".iso")) for f in self.project.required_files) or
            self.project.original_platform in ["Nintendo 64", "Game Boy", "Game Boy Advance", "Sega Genesis / Mega Drive"]
        )

        if is_rom_game:
            rom_card = QFrame()
            rom_card.setStyleSheet("background-color: #1e1b4b; border: 1px solid #6366f1; border-radius: 10px; padding: 14px;")
            r_layout = QVBoxLayout(rom_card)
            r_layout.setSpacing(8)

            r_title = QLabel("🎯 Automatischer ROM-Abgleich (Auto-Erkennung & Konverter)")
            r_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #a5b4fc;")
            r_layout.addWidget(r_title)

            r_hint = QLabel(
                "Durchsucht dein ROM-Verzeichnis automatisch nach der passenden Spieldatei, "
                "entpackt Zip-Archive und wandelt das Byte-Format (.v64/.n64 zu .z64) in Millisekunden um."
            )
            r_hint.setStyleSheet("font-size: 11px; color: #cbd5e1;")
            r_hint.setWordWrap(True)
            r_layout.addWidget(r_hint)

            r_row = QHBoxLayout()
            self.rom_dir_input = QLineEdit(self.library_mgr.get_roms_directory())
            r_row.addWidget(self.rom_dir_input, 1)

            r_browse_btn = QPushButton("Ordner...")
            r_browse_btn.setProperty("class", "secondary-btn")
            r_browse_btn.clicked.connect(self._browse_rom_dir)
            r_row.addWidget(r_browse_btn)

            r_scan_btn = QPushButton("⚡ ROM automatisch abgleichen & einbinden")
            r_scan_btn.setProperty("class", "primary-btn")
            r_scan_btn.clicked.connect(self._run_auto_rom_import)
            r_row.addWidget(r_scan_btn)

            r_layout.addLayout(r_row)

            # Suggest candidate dirs if found
            candidates = RomAutoMatcher.get_candidate_rom_dirs()
            if candidates:
                cand_box = QHBoxLayout()
                cand_title = QLabel("Gefundene Verzeichnisse:")
                cand_title.setStyleSheet("font-size: 11px; color: #94a3b8;")
                cand_box.addWidget(cand_title)
                for cd in candidates[:3]:
                    c_btn = QPushButton(os.path.basename(cd) or cd)
                    c_btn.setProperty("class", "secondary-btn")
                    c_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
                    c_btn.clicked.connect(lambda checked, path=cd: self.rom_dir_input.setText(path))
                    cand_box.addWidget(c_btn)
                cand_box.addStretch(1)
                r_layout.addLayout(cand_box)

            layout.addWidget(rom_card)

        # -------------------------------------------------------------
        # Section 5: Option D - Custom URL Downloader (Cloud / Backup)
        # -------------------------------------------------------------
        url_card = QFrame()
        url_card.setStyleSheet("background-color: #131b2e; border: 1px solid #1e293b; border-radius: 10px; padding: 14px;")
        u_layout = QVBoxLayout(url_card)
        u_layout.setSpacing(8)

        u_title = QLabel("🌐 Spieldateien / ROM von URL herunterladen")
        u_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        u_layout.addWidget(u_title)

        u_hint = QLabel("Gib eine direkte Download-URL (z. B. von deiner Nextcloud, Server oder Backup) ein:")
        u_hint.setStyleSheet("font-size: 11px; color: #94a3b8;")
        u_layout.addWidget(u_hint)

        u_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://mein-server.de/spiele/baserom.z64 (oder .zip)")
        u_row.addWidget(self.url_input, 1)

        dl_url_btn = QPushButton("⬇ Download")
        dl_url_btn.setProperty("class", "primary-btn")
        dl_url_btn.clicked.connect(self._download_from_custom_url)
        u_row.addWidget(dl_url_btn)
        u_layout.addLayout(u_row)

        layout.addWidget(url_card)

        # ⚖️ Legal Note
        legal_card = QFrame()
        legal_card.setStyleSheet("background-color: #0c1220; border: 1px solid #1e293b; border-radius: 8px; padding: 10px;")
        l_layout = QVBoxLayout(legal_card)
        l_layout.setSpacing(4)
        l_title = QLabel("⚖️ Rechtlicher Hinweis zu ROM-Downloads:")
        l_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")
        l_layout.addWidget(l_title)
        l_desc = QLabel(
            "Kommerzielle ROMs (Nintendo 64 etc.) unterliegen dem Urheberrecht. "
            "Recomp Center bietet deshalb die 100% legale Automatisierung: Deine vorhandenen ROMs auf der Festplatte "
            "werden per 1-Klick gefunden, entpackt, bei Bedarf vom Doctor V64-Format (.v64) in Big-Endian (.z64) umgewandelt "
            "und als baserom eingerichtet."
        )
        l_desc.setStyleSheet("font-size: 10px; color: #64748b;")
        l_desc.setWordWrap(True)
        l_layout.addWidget(l_desc)
        layout.addWidget(legal_card)

        # Progress bar & Status
        self.status_box = QFrame()
        self.status_box.setStyleSheet("background-color: #0c1220; border-radius: 8px; padding: 10px;")
        self.status_box.setVisible(False)
        st_layout = QVBoxLayout(self.status_box)

        self.dl_progress = QProgressBar()
        st_layout.addWidget(self.dl_progress)

        self.dl_status_lbl = QLabel("Warte auf Download...")
        self.dl_status_lbl.setStyleSheet("font-size: 12px; color: #38bdf8;")
        st_layout.addWidget(self.dl_status_lbl)

        layout.addWidget(self.status_box)

        self._refresh_file_list()

        # -------------------------------------------------------------
        # Bottom Controls
        # -------------------------------------------------------------
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        manual_import_btn = QPushButton("📂 Lokale Datei(en) wählen...")
        manual_import_btn.setProperty("class", "secondary-btn")
        manual_import_btn.clicked.connect(self._import_manual_files)
        bottom_bar.addWidget(manual_import_btn)

        open_folder_btn = QPushButton("📁 Ordner öffnen")
        open_folder_btn.setProperty("class", "secondary-btn")
        open_folder_btn.clicked.connect(self._open_folder)
        bottom_bar.addWidget(open_folder_btn)

        bottom_bar.addStretch(1)

        close_btn = QPushButton("Fertig")
        close_btn.setProperty("class", "primary-btn")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)

        root_layout.addLayout(bottom_bar)

    def _refresh_file_list(self):
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        header_lbl = QLabel("📋 Status der Spieldateien:")
        header_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        self.files_layout.addWidget(header_lbl)

        target_dir = self._get_target_dir()

        if self.project.required_assets_desc:
            desc = QLabel(f"<b>Bedarf:</b> {self.project.required_assets_desc}")
            desc.setStyleSheet("color: #38bdf8; font-size: 12px;")
            desc.setWordWrap(True)
            self.files_layout.addWidget(desc)

        if not self.project.required_files:
            lbl = QLabel("ℹ️ Dieses Projekt erfordert keine festen Dateinamen oder erzeugt diese beim ersten Start.")
            lbl.setStyleSheet("color: #a7f3d0; font-size: 12px;")
            self.files_layout.addWidget(lbl)
            return

        has_all, missing = self.library_mgr.check_game_assets(self.project)

        for req in self.project.required_files:
            is_present = req not in missing
            row = QHBoxLayout()
            if is_present:
                status_icon = QLabel("✅")
                status_text = QLabel(f"<b>{req}</b> (Gefunden)")
                status_text.setStyleSheet("color: #10b981; font-size: 12px;")
            else:
                status_icon = QLabel("❌")
                status_text = QLabel(f"<b>{req}</b> (Fehlt im Spieleordner)")
                status_text.setStyleSheet("color: #f87171; font-size: 12px;")
            row.addWidget(status_icon)
            row.addWidget(status_text, 1)
            self.files_layout.addLayout(row)

        dir_lbl = QLabel(f"Zielverzeichnis: <span style='color:#64748b'>{target_dir}</span>")
        dir_lbl.setTextFormat(Qt.TextFormat.RichText)
        dir_lbl.setStyleSheet("font-size: 11px; margin-top: 6px;")
        self.files_layout.addWidget(dir_lbl)

    def _start_asset_download(self, url: str, filename: str):
        target_dir = self._get_target_dir()
        self.status_box.setVisible(True)
        self.dl_status_lbl.setText("Initialisiere Download...")
        self.dl_progress.setValue(0)

        self.active_worker = AssetDownloadWorker(url, target_dir, filename)
        self.active_worker.progress.connect(lambda cur, tot, s: self._on_download_progress(cur, tot, s))
        self.active_worker.status.connect(self.dl_status_lbl.setText)
        self.active_worker.finished.connect(self._on_download_finished)
        self.active_worker.start()

    def _on_download_progress(self, current: int, total: int, speed: str):
        if total > 0:
            self.dl_progress.setValue(int((current / total) * 100))

    def _browse_rom_dir(self):
        d = QFileDialog.getExistingDirectory(self, "ROM-Verzeichnis auswählen", self.rom_dir_input.text() or os.path.expanduser("~"))
        if d:
            self.rom_dir_input.setText(d)
            self.library_mgr.set_roms_directory(d)

    def _run_auto_rom_import(self):
        rom_dir = self.rom_dir_input.text().strip()
        if not rom_dir or not os.path.exists(rom_dir):
            QMessageBox.warning(self, "Verzeichnis ungültig", "Bitte wähle ein existierendes ROM-Verzeichnis aus.")
            return

        self.library_mgr.set_roms_directory(rom_dir)
        target_dir = self._get_target_dir()

        success, msg = RomAutoMatcher.auto_import(self.project, rom_dir, target_dir)
        if success:
            QMessageBox.information(self, "ROM-Abgleich erfolgreich", msg)
            self._refresh_file_list()
        else:
            QMessageBox.warning(self, "Keine passende ROM gefunden", msg)

    def _on_download_finished(self, success: bool, msg: str):
        if success:
            target_dir = self._get_target_dir()
            # Post-download: If it was a ROM or zip, try auto-importing/converting
            try:
                RomAutoMatcher.auto_import(self.project, target_dir, target_dir)
            except Exception:
                pass

            self.dl_status_lbl.setText("✅ " + msg)
            QMessageBox.information(self, "Erfolg", msg)
            self._refresh_file_list()
        else:
            self.dl_status_lbl.setText("❌ " + msg)
            QMessageBox.critical(self, "Download-Fehler", msg)

    def _import_from_steam(self, steam_game_dir: str):
        target_dir = self._get_target_dir()
        copied, msg = SteamGOGScanner.copy_from_steam(steam_game_dir, target_dir, self.project.required_files)
        if copied > 0:
            QMessageBox.information(self, "Import erfolgreich", f"{copied} Spieldatei(en) aus deiner Steam/GOG Bibliothek importiert!")
            self._refresh_file_list()
        else:
            QMessageBox.warning(self, "Keine Dateien kopiert", f"Konnte keine passenden Dateien finden: {msg}")

    def _download_from_custom_url(self):
        url = self.url_input.text().strip()
        if not url or not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Ungültige URL", "Bitte gib eine gültige HTTP/HTTPS URL ein.")
            return

        filename = os.path.basename(url.split("?")[0]) or "spieldateien.zip"
        self._start_asset_download(url, filename)

    def _import_manual_files(self):
        target_dir = self._get_target_dir()
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Wähle Spieldateien / ROM zum Importieren",
            os.path.expanduser("~"),
            "Alle Dateien (*.*);;ROMs (*.z64 *.n64 *.iso *.bin *.rom);;Archive (*.mpq *.dat *.rsdk *.zip)"
        )

        if not files:
            return

        copied_count = 0
        for f in files:
            try:
                dest = os.path.join(target_dir, os.path.basename(f))
                shutil.copy2(f, dest)
                copied_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Fehler beim Kopieren", f"Konnte {f} nicht kopieren: {e}")

        if copied_count > 0:
            QMessageBox.information(self, "Import erfolgreich", f"{copied_count} Datei(en) erfolgreich kopiert!")
            self._refresh_file_list()

    def _open_folder(self):
        d = self._get_target_dir()
        GameLauncher.open_game_folder(d)
