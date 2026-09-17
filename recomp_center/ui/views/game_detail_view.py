"""Detailed view for an individual Recomp/Decomp project."""

import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextBrowser, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from ...core.models import GameProject, ProjectType, ReleaseInfo
from ...core.library import LibraryManager
from ...core.github_client import GitHubClient
from ...core.launcher import GameLauncher
from ..widgets.asset_dialog import AssetDialog


class ReleaseCheckWorker(QThread):
    release_found = pyqtSignal(object)  # Optional[ReleaseInfo]

    def __init__(self, client: GitHubClient, project: GameProject):
        super().__init__()
        self.client = client
        self.project = project

    def run(self):
        rel = self.client.get_latest_release(self.project)
        self.release_found.emit(rel)


class GameDetailView(QWidget):
    back_requested = pyqtSignal()
    download_requested = pyqtSignal(str, object)  # project_id, ReleaseInfo
    launch_requested = pyqtSignal(str)
    compile_requested = pyqtSignal(str)

    def __init__(self, project: GameProject, library_mgr: LibraryManager, github_client: GitHubClient, parent=None):
        super().__init__(parent)
        self.project = project
        self.library_mgr = library_mgr
        self.github_client = github_client
        self.latest_release = None

        self._build_ui()
        self._check_release()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Top Bar: Back Button
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Zurück")
        back_btn.setProperty("class", "secondary-btn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)

        top_bar.addStretch(1)

        if self.project.github_url:
            gh_btn = QPushButton("🌐 GitHub Repository")
            gh_btn.setProperty("class", "secondary-btn")
            gh_btn.clicked.connect(lambda: webbrowser.open(self.project.github_url))
            top_bar.addWidget(gh_btn)

        main_layout.addLayout(top_bar)

        # Scrollable Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        # Header Hero Card
        header_card = QFrame()
        header_card.setProperty("class", "detail-header")
        h_layout = QHBoxLayout(header_card)
        h_layout.setSpacing(20)

        # Big Icon
        icon_lbl = QLabel(self.project.icon_text)
        icon_lbl.setStyleSheet(f"""
            background-color: {self.project.color_accent}22;
            border: 2px solid {self.project.color_accent}66;
            border-radius: 16px;
            font-size: 40px;
        """)
        icon_lbl.setFixedSize(76, 76)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(icon_lbl)

        # Title & Meta
        meta_box = QVBoxLayout()
        meta_box.setSpacing(4)

        title_lbl = QLabel(self.project.name)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        meta_box.addWidget(title_lbl)

        sub_lbl = QLabel(f"Entwickler: <b>{self.project.author}</b> • Plattform: <b>{self.project.original_platform}</b> • Typ: <b>{self.project.project_type.value}</b>")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        meta_box.addWidget(sub_lbl)

        h_layout.addLayout(meta_box, 1)

        # Action Buttons on Header
        self.action_box = QVBoxLayout()
        self.action_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.action_box.setSpacing(8)

        self.primary_action_btn = QPushButton("Lade Release-Info...")
        self.primary_action_btn.setEnabled(False)
        self.primary_action_btn.setMinimumWidth(170)
        self.primary_action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_box.addWidget(self.primary_action_btn)

        h_layout.addLayout(self.action_box)
        layout.addWidget(header_card)

        # Dynamic ROM / Assets Box
        self.asset_box = QFrame()
        self.asset_layout = QHBoxLayout(self.asset_box)
        self.asset_layout.setContentsMargins(16, 14, 16, 14)
        self._refresh_asset_box()
        layout.addWidget(self.asset_box)

        # Description Section
        desc_box = QFrame()
        desc_box.setStyleSheet("background-color: #111726; border: 1px solid #1e293b; border-radius: 12px; padding: 18px;")
        desc_layout = QVBoxLayout(desc_box)

        desc_title = QLabel("Über dieses Projekt")
        desc_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff; margin-bottom: 6px;")
        desc_layout.addWidget(desc_title)

        body_lbl = QLabel(self.project.full_desc or self.project.short_desc)
        body_lbl.setStyleSheet("font-size: 13px; color: #cbd5e1; line-height: 1.6;")
        body_lbl.setWordWrap(True)
        desc_layout.addWidget(body_lbl)

        layout.addWidget(desc_box)

        # Release Details / Changelog Box
        self.rel_box = QFrame()
        self.rel_box.setStyleSheet("background-color: #111726; border: 1px solid #1e293b; border-radius: 12px; padding: 18px;")
        self.rel_layout = QVBoxLayout(self.rel_box)

        self.rel_title = QLabel("📦 Release-Informationen")
        self.rel_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        self.rel_layout.addWidget(self.rel_title)

        self.rel_info_lbl = QLabel("Informationen werden von GitHub abgerufen...")
        self.rel_info_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 4px;")
        self.rel_layout.addWidget(self.rel_info_lbl)

        layout.addWidget(self.rel_box)
        layout.addStretch(1)

    def _refresh_asset_box(self):
        # Clear layout
        while self.asset_layout.count():
            item = self.asset_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                subl = item.layout()
                while subl.count():
                    si = subl.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        asset_info = QVBoxLayout()
        asset_info.setSpacing(4)

        if not self.project.required_files:
            self.asset_box.setStyleSheet("background-color: #111726; border: 1px solid #1e293b; border-radius: 12px;")
            title = QLabel("💾 Spieldaten: Keine externen ROM-Dateien erforderlich")
            title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
            desc = QLabel("Dieses Projekt enthält alle benötigten Spieldaten oder extrahiert diese automatisch beim ersten Start.")
            desc.setStyleSheet("font-size: 12px; color: #94a3b8;")
            desc.setWordWrap(True)
            asset_info.addWidget(title)
            asset_info.addWidget(desc)
            self.asset_layout.addLayout(asset_info, 1)
            return

        has_assets, missing = self.library_mgr.check_game_assets(self.project)
        if has_assets:
            self.asset_box.setStyleSheet("""
                background-color: #042217;
                border: 1px solid #059669;
                border-radius: 12px;
            """)
            title = QLabel("✅ Alle erforderlichen Spieldateien / ROMs vorhanden!")
            title.setStyleSheet("font-size: 14px; font-weight: 800; color: #34d399;")
            desc = QLabel(f"Erforderliche Dateien ({', '.join(self.project.required_files)}) wurden im Spielverzeichnis gefunden. Das Spiel ist startbereit.")
            desc.setStyleSheet("font-size: 12px; color: #a7f3d0;")
            desc.setWordWrap(True)
            asset_info.addWidget(title)
            asset_info.addWidget(desc)
            self.asset_layout.addLayout(asset_info, 1)

            manage_btn = QPushButton("Dateien verwalten")
            manage_btn.setProperty("class", "secondary-btn")
            manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            manage_btn.clicked.connect(self._open_assets)
            self.asset_layout.addWidget(manage_btn)
        else:
            self.asset_box.setStyleSheet("""
                background-color: #2e1505;
                border: 1px solid #d97706;
                border-radius: 12px;
            """)
            title = QLabel("⚠️ Original-Spieldateien / ROMs noch nicht hinterlegt")
            title.setStyleSheet("font-size: 14px; font-weight: 800; color: #fbbf24;")
            desc_text = self.project.required_assets_desc or f"Fehlend: {', '.join(missing)}"
            desc = QLabel(desc_text)
            desc.setStyleSheet("font-size: 12px; color: #fde68a;")
            desc.setWordWrap(True)
            asset_info.addWidget(title)
            asset_info.addWidget(desc)
            self.asset_layout.addLayout(asset_info, 1)

            manage_btn = QPushButton("ROM bereitstellen...")
            manage_btn.setProperty("class", "primary-btn")
            manage_btn.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b);
                color: #ffffff;
                border: 1px solid #fbbf24;
            """)
            manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            manage_btn.clicked.connect(self._open_assets)
            self.asset_layout.addWidget(manage_btn)

    def _check_release(self):
        if not self.project.has_binary_releases:
            self.primary_action_btn.setText("🔨 Aus Source kompilieren")
            self.primary_action_btn.setProperty("class", "primary-btn")
            self.primary_action_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b); color: #ffffff; font-weight: bold; border: 1px solid #fbbf24;")
            self.primary_action_btn.setEnabled(True)
            self.primary_action_btn.clicked.connect(lambda: self.compile_requested.emit(self.project.id))
            self.rel_info_lbl.setText("Dies ist ein Source-Decompilierungs-Projekt. Klicke auf 'Aus Source kompilieren', um den Code herunterzuladen und nativ zu bauen.")
            return

        is_installed = self.library_mgr.is_installed(self.project.id)
        if is_installed:
            self._setup_installed_state()
        else:
            self.primary_action_btn.setText("Verbindung prüfen...")

        # Add optional compile from source button
        if self.project.can_compile:
            src_compile_btn = QPushButton("🔨 Aus Source bauen")
            src_compile_btn.setProperty("class", "secondary-btn")
            src_compile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            src_compile_btn.clicked.connect(lambda: self.compile_requested.emit(self.project.id))
            self.action_box.addWidget(src_compile_btn)

        # Run background worker to query GitHub
        self.worker = ReleaseCheckWorker(self.github_client, self.project)
        self.worker.release_found.connect(self._on_release_found)
        self.worker.start()

    def _on_release_found(self, release: ReleaseInfo):
        self.latest_release = release
        is_installed = self.library_mgr.is_installed(self.project.id)

        if release:
            size_mb = f"• {release.asset_size / (1024*1024):.1f} MB" if release.asset_size else ""
            pub_date = release.published_at[:10] if release.published_at else "k. A."
            self.rel_info_lbl.setText(
                f"<div style='font-size: 13px; line-height: 1.6;'>"
                f"Neueste Version: <b style='color: #38bdf8;'>{release.tag_name}</b> {size_mb}<br>"
                f"Datei: <code style='color: #cbd5e1;'>{release.asset_name}</code><br>"
                f"Veröffentlicht am: {pub_date}"
                f"</div>"
            )
            self.rel_info_lbl.setTextFormat(Qt.TextFormat.RichText)

            if is_installed:
                installed_game = self.library_mgr.get_installed(self.project.id)
                self._setup_installed_state()
                if installed_game and installed_game.version != release.tag_name:
                    update_btn = QPushButton(f"⬆ Aktualisieren auf {release.tag_name}")
                    update_btn.setProperty("class", "primary-btn")
                    update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    update_btn.clicked.connect(lambda: self.download_requested.emit(self.project.id, release))
                    self.action_box.addWidget(update_btn)
            else:
                self.primary_action_btn.setText(f"⬇ Installieren ({release.tag_name})")
                self.primary_action_btn.setProperty("class", "primary-btn")
                self.primary_action_btn.setEnabled(True)
                try:
                    self.primary_action_btn.clicked.disconnect()
                except Exception:
                    pass
                self.primary_action_btn.clicked.connect(lambda: self.download_requested.emit(self.project.id, release))
        else:
            if not is_installed:
                self.primary_action_btn.setText("Website / GitHub öffnen")
                self.primary_action_btn.setProperty("class", "secondary-btn")
                self.primary_action_btn.setEnabled(True)
                try:
                    self.primary_action_btn.clicked.disconnect()
                except Exception:
                    pass
                self.primary_action_btn.clicked.connect(lambda: webbrowser.open(self.project.github_url))
                self.rel_info_lbl.setText("Kein direktes Linux-Binary Release im GitHub-Repository gefunden oder API-Ratenlimit erreicht.")

    def _setup_installed_state(self):
        try:
            self.primary_action_btn.clicked.disconnect()
        except Exception:
            pass
        self.primary_action_btn.setText("▶ Spielen")
        self.primary_action_btn.setProperty("class", "success-btn")
        self.primary_action_btn.setEnabled(True)
        self.primary_action_btn.clicked.connect(lambda: self.launch_requested.emit(self.project.id))

    def _open_assets(self):
        dlg = AssetDialog(self.project, self.library_mgr, self)
        dlg.exec()
        self._refresh_asset_box()

