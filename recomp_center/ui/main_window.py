"""Main application window for Recomp Center."""

import os
import tempfile
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from ..core.library import LibraryManager
from ..core.github_client import GitHubClient
from ..core.downloader import DownloadWorker
from ..core.extractor import Extractor
from ..core.launcher import GameLauncher
from ..data.catalog import get_all_projects, get_project_by_id

from .views.explore_view import ExploreView
from .views.library_view import LibraryView
from .views.game_detail_view import GameDetailView
from .views.downloads_view import DownloadsView
from .views.settings_view import SettingsView
from .widgets.asset_dialog import AssetDialog
from .widgets.compile_dialog import CompileDialog
from ..updater import UpdateDialog, UpdateCheckerWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recomp Center – Recomp & Decomp Hub")
        self.resize(1150, 750)
        self.setMinimumSize(960, 620)

        # Core state
        self.library_mgr = LibraryManager()
        self.github_client = GitHubClient(self.library_mgr.get_github_token())
        self.launcher = GameLauncher(self.library_mgr)
        self.all_projects = get_all_projects()
        self.active_download_worker = None
        self.current_downloading_proj = None
        self.current_downloading_rel = None
        self._bg_updater = None

        self._build_ui()
        self.start_background_update_check(force=False)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. Left Sidebar
        # -------------------------------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 20, 14, 20)
        side_layout.setSpacing(8)

        # Brand / Logo
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        logo_lbl = QLabel("⚡")
        logo_lbl.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #0369a1);
            border: 1px solid #38bdf8;
            border-radius: 10px;
            font-size: 22px;
            padding: 4px;
        """)
        logo_lbl.setFixedSize(40, 40)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(logo_lbl)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        app_name = QLabel("RECOMP")
        app_name.setStyleSheet("font-size: 17px; font-weight: 900; letter-spacing: 1.5px; color: #ffffff;")
        app_sub = QLabel("CENTER")
        app_sub.setStyleSheet("font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #38bdf8;")
        brand_text.addWidget(app_name)
        brand_text.addWidget(app_sub)
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)

        side_layout.addLayout(brand_row)
        side_layout.addSpacing(20)

        # Section Label
        menu_lbl = QLabel("NAVIGATION")
        menu_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #475569; letter-spacing: 1.5px; padding-left: 6px;")
        side_layout.addWidget(menu_lbl)

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("explore", "🔍  Katalog", self._show_explore),
            ("library", "🎮  Bibliothek", self._show_library),
            ("downloads", "📥  Downloads", self._show_downloads),
            ("settings", "⚙️  Einstellungen", self._show_settings),
        ]

        for nav_id, label, handler in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "nav-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(handler)
            side_layout.addWidget(btn)
            self.nav_buttons[nav_id] = btn

        side_layout.addStretch(1)

        # Status footer card in sidebar
        footer_card = QFrame()
        footer_card.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        f_layout = QVBoxLayout(footer_card)
        f_layout.setContentsMargins(8, 8, 8, 8)
        f_layout.setSpacing(4)

        foot_lbl = QLabel("SYSTEM STATUS")
        foot_lbl.setStyleSheet("font-size: 9px; font-weight: 800; color: #475569; letter-spacing: 1px;")
        f_layout.addWidget(foot_lbl)

        self.side_status = QLabel("Lade Status...")
        self.side_status.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 600;")
        f_layout.addWidget(self.side_status)

        self.btn_check_updates = QPushButton("Auf Updates prüfen...")
        self.btn_check_updates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check_updates.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 8px;
                margin-top: 4px;
            }
            QPushButton:hover {
                background: #0284c7;
                color: #ffffff;
                border-color: #38bdf8;
            }
        """)
        self.btn_check_updates.clicked.connect(self.show_update_dialog)
        f_layout.addWidget(self.btn_check_updates)

        side_layout.addWidget(footer_card)
        root_layout.addWidget(sidebar)

        # -------------------------------------------------------------
        # 2. Central Content Area (StackedWidget)
        # -------------------------------------------------------------
        content_container = QWidget()
        content_container.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_container, 1)

        # Initialize Views
        self.explore_view = ExploreView(self.all_projects, self.library_mgr)
        self.explore_view.project_selected.connect(self._show_project_detail)
        self.explore_view.install_requested.connect(self._start_install_from_id)
        self.explore_view.launch_requested.connect(self._launch_game_from_id)
        self.explore_view.compile_requested.connect(self._start_compilation_from_id)
        self.stack.addWidget(self.explore_view)  # Index 0

        self.library_view = LibraryView(self.library_mgr)
        self.library_view.explore_requested.connect(self._show_explore)
        self.library_view.launch_requested.connect(self._launch_game_from_id)
        self.stack.addWidget(self.library_view)  # Index 1

        self.downloads_view = DownloadsView()
        self.downloads_view.cancel_requested.connect(self._cancel_download)
        self.stack.addWidget(self.downloads_view)  # Index 2

        self.settings_view = SettingsView(self.library_mgr)
        self.stack.addWidget(self.settings_view)  # Index 3

        # Default to Explore view
        self._set_active_nav("explore")
        self.stack.setCurrentIndex(0)
        self._update_sidebar_badges()

    def _update_sidebar_badges(self):
        """Refreshes sidebar badges, installed count, active downloads, and disk storage."""
        inst_count = len(self.library_mgr.installed_games)
        if "library" in self.nav_buttons:
            self.nav_buttons["library"].setText(f"🎮  Bibliothek  ({inst_count})")
        if "downloads" in self.nav_buttons:
            if self.active_download_worker and self.active_download_worker.isRunning():
                self.nav_buttons["downloads"].setText("📥  Downloads  (1 aktiv)")
            else:
                self.nav_buttons["downloads"].setText("📥  Downloads")

        # Calculate disk storage used
        total_bytes = 0
        for game in self.library_mgr.installed_games.values():
            if game.install_path and os.path.exists(game.install_path):
                for root, dirs, files in os.walk(game.install_path):
                    for f in files:
                        try:
                            total_bytes += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
        if total_bytes > 1024 * 1024 * 1024:
            size_str = f"{total_bytes / (1024*1024*1024):.1f} GB"
        elif total_bytes > 1024 * 1024:
            size_str = f"{total_bytes / (1024*1024):.1f} MB"
        else:
            size_str = f"{total_bytes / 1024:.0f} KB"
        self.side_status.setText(f"🎮 {inst_count} Spiele • 💾 {size_str}")

    # -------------------------------------------------------------
    # Navigation Handlers
    # -------------------------------------------------------------
    def _set_active_nav(self, active_id: str):
        for nav_id, btn in self.nav_buttons.items():
            btn.setChecked(nav_id == active_id)

    def _show_explore(self):
        self._set_active_nav("explore")
        self.explore_view.refresh_cards()
        self._update_sidebar_badges()
        self.stack.setCurrentWidget(self.explore_view)

    def _show_library(self):
        self._set_active_nav("library")
        self.library_view.refresh_library()
        self._update_sidebar_badges()
        self.stack.setCurrentWidget(self.library_view)

    def _show_downloads(self):
        self._set_active_nav("downloads")
        self._update_sidebar_badges()
        self.stack.setCurrentWidget(self.downloads_view)

    def _show_settings(self):
        self._set_active_nav("settings")
        self._update_sidebar_badges()
        self.stack.setCurrentWidget(self.settings_view)

    def _show_project_detail(self, project_id: str):
        proj = get_project_by_id(project_id)
        if not proj:
            return

        detail = GameDetailView(proj, self.library_mgr, self.github_client)
        detail.back_requested.connect(self._show_explore)
        detail.download_requested.connect(self._start_download)
        detail.launch_requested.connect(self._launch_game_from_id)
        detail.compile_requested.connect(self._start_compilation_from_id)

        self.stack.addWidget(detail)
        self.stack.setCurrentWidget(detail)

    def _start_compilation_from_id(self, project_id: str):
        proj = get_project_by_id(project_id)
        if not proj:
            return

        dlg = CompileDialog(proj, self.library_mgr, self)
        dlg.launch_requested.connect(self._launch_game_from_id)
        dlg.exec()

        self.library_view.refresh_library()
        self.explore_view.refresh_cards()
        self._update_sidebar_badges()

    # -------------------------------------------------------------
    # Download & Installation Pipeline
    # -------------------------------------------------------------
    def _start_install_from_id(self, project_id: str):
        proj = get_project_by_id(project_id)
        if not proj:
            return
        self._show_project_detail(project_id)

    def _start_download(self, project_id: str, release_info):
        if self.active_download_worker and self.active_download_worker.isRunning():
            QMessageBox.warning(self, "Download läuft bereits", "Es wird derzeit bereits ein anderes Spiel heruntergeladen.")
            return

        proj = get_project_by_id(project_id)
        if not proj or not release_info:
            return

        self.current_downloading_proj = proj
        self.current_downloading_rel = release_info

        # Show downloads view
        self._show_downloads()
        self.downloads_view.set_active_download(f"{proj.name} ({release_info.tag_name})")

        # Start download in temporary dir
        temp_dir = os.path.join(tempfile.gettempdir(), "recomp_downloads")
        os.makedirs(temp_dir, exist_ok=True)

        self.active_download_worker = DownloadWorker(
            url=release_info.download_url,
            target_dir=temp_dir,
            filename=release_info.asset_name,
            headers=self.github_client._get_headers()
        )
        self.active_download_worker.progress.connect(self.downloads_view.update_progress)
        self.active_download_worker.status.connect(self.downloads_view.update_status)
        self.active_download_worker.finished.connect(self._on_download_finished)
        self.active_download_worker.error.connect(self._on_download_error)
        self.active_download_worker.start()
        self._update_sidebar_badges()

    def _cancel_download(self):
        if self.active_download_worker:
            self.active_download_worker.cancel()
            self.downloads_view.mark_finished(
                self.current_downloading_proj.name if self.current_downloading_proj else "Download",
                False,
                "Vom Nutzer abgebrochen."
            )
            self._update_sidebar_badges()

    def _on_download_finished(self, archive_path: str):
        proj = self.current_downloading_proj
        rel = self.current_downloading_rel

        if not proj or not rel:
            return

        self.downloads_view.update_status("Extrahiere und installiere Dateien...")

        games_dir = self.library_mgr.get_games_directory()
        target_game_dir = os.path.join(games_dir, proj.id)

        success, exe_path, err = Extractor.install_package(
            archive_path=archive_path,
            destination_dir=target_game_dir,
            executable_hints=proj.executable_hints
        )

        # Cleanup temp archive
        if os.path.exists(archive_path):
            try:
                os.remove(archive_path)
            except Exception:
                pass

        if success:
            installed = self.library_mgr.register_installed(
                game_id=proj.id,
                name=proj.name,
                version=rel.tag_name,
                install_path=target_game_dir,
                exe_path=exe_path
            )

            # Auto-create desktop shortcut if configured
            if self.library_mgr.settings.get("create_desktop_shortcuts", True):
                self.library_mgr.create_desktop_entry(proj)

            self.downloads_view.mark_finished(proj.name, True, f"Installiert nach: {target_game_dir}")
            self.explore_view.refresh_cards()
            self.library_view.refresh_library()
            self._update_sidebar_badges()

            # Check if assets are needed and notify user
            if proj.required_files:
                has_assets, missing = self.library_mgr.check_game_assets(proj)
                if not has_assets:
                    dlg = AssetDialog(proj, self.library_mgr, self)
                    dlg.exec()
            else:
                QMessageBox.information(
                    self,
                    "Installation abgeschlossen",
                    f"'{proj.name}' wurde erfolgreich installiert und ist startbereit!"
                )
        else:
            self.downloads_view.mark_finished(proj.name, False, f"Extraktionsfehler: {err}")
            self._update_sidebar_badges()
            QMessageBox.critical(self, "Installationsfehler", f"Konnte {proj.name} nicht extrahieren: {err}")

    def _on_download_error(self, err_msg: str):
        proj_name = self.current_downloading_proj.name if self.current_downloading_proj else "Spiel"
        self.downloads_view.mark_finished(proj_name, False, err_msg)
        self._update_sidebar_badges()
        QMessageBox.critical(self, "Download-Fehler", err_msg)

    # -------------------------------------------------------------
    # Launch Game
    # -------------------------------------------------------------
    def _launch_game_from_id(self, game_id: str):
        installed = self.library_mgr.get_installed(game_id)
        proj = get_project_by_id(game_id)

        if not installed:
            QMessageBox.warning(self, "Nicht installiert", "Dieses Spiel ist noch nicht installiert.")
            return

        # Check required assets
        if proj and proj.required_files:
            has_assets, missing = self.library_mgr.check_game_assets(proj)
            if not has_assets:
                reply = QMessageBox.question(
                    self,
                    "Erforderliche Spieldateien fehlen",
                    f"Für '{proj.name}' fehlen noch folgende Dateien:\n- " + "\n- ".join(missing) +
                    "\n\nMöchtest du die Spieldateien / ROM jetzt über den Assistenten bereitstellen?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    dlg = AssetDialog(proj, self.library_mgr, self)
                    dlg.exec()
                    return

        # Launch
        ok, msg = self.launcher.launch(installed)
        if not ok:
            QMessageBox.critical(self, "Startfehler", msg)
        else:
            self.library_view.refresh_library()

    # -------------------------------------------------------------
    # In-App GitHub Updater Integration (Cachy Security Suite Pattern)
    # -------------------------------------------------------------
    def start_background_update_check(self, force: bool = False):
        """Silently checks for updates in the background on startup."""
        import time
        from PyQt6.QtCore import QSettings

        settings = QSettings("RecompCenter", "RecompCenter")
        last_check = settings.value("updater/last_background_check", 0, type=int)
        now = int(time.time())

        # Check at most once every 24 hours in background, unless forced
        if not force and (now - last_check < 86400):
            return

        self._bg_updater = UpdateCheckerWorker()
        self._bg_updater.finished.connect(self._on_bg_update_finished)
        self._bg_updater.start()

    def _on_bg_update_finished(self, info):
        import time
        from PyQt6.QtCore import QSettings

        settings = QSettings("RecompCenter", "RecompCenter")
        settings.setValue("updater/last_background_check", int(time.time()))

        pending = info.total_updates_pending()
        if pending > 0:
            self.btn_check_updates.setText(f"● Update verfügbar (v{info.app_remote})")
            self.btn_check_updates.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #c2410c);
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: 700;
                    border: 1px solid #f97316;
                    border-radius: 6px;
                    padding: 6px 8px;
                    margin-top: 4px;
                }
                QPushButton:hover {
                    background: #ea580c;
                    border-color: #fdba74;
                }
            """)
            self.btn_check_updates.setToolTip(
                f"Neues Recomp Center Update verfügbar:\n• Version: v{info.app_remote}\nKlicken zum Öffnen des Update-Centers."
            )

    def show_update_dialog(self):
        dlg = UpdateDialog(self)
        dlg.exec()

        # Reset button styling after dialog is closed
        self.btn_check_updates.setText("Auf Updates prüfen...")
        self.btn_check_updates.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #e2e8f0;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 8px;
                margin-top: 4px;
            }
            QPushButton:hover {
                background: #0284c7;
                color: #ffffff;
                border-color: #38bdf8;
            }
        """)
        self.btn_check_updates.setToolTip("Update- & System-Center öffnen")

