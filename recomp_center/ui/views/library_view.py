"""Library view for managing installed Recomp/Decomp games with system grouping and sorting."""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...core.library import LibraryManager
from ...core.launcher import GameLauncher
from ...core.models import InstalledGame, GameProject
from ...data.catalog import get_project_by_id, SYSTEM_ORDER, SYSTEM_ICONS, get_system_group
from ..widgets.asset_dialog import AssetDialog


class LibraryView(QWidget):
    explore_requested = pyqtSignal()
    launch_requested = pyqtSignal(str)

    def __init__(self, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.library_mgr = library_mgr
        self.current_sort = "system"
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title & Stats
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Meine Bibliothek")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #f8fafc;")
        title_box.addWidget(title)

        self.subtitle = QLabel("Installierte Recomp- & Decomp-Ports auf diesem PC.")
        self.subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(self.subtitle)
        header_row.addLayout(title_box, 1)

        open_dir_btn = QPushButton("📁 Spiele-Ordner öffnen")
        open_dir_btn.setProperty("class", "secondary-btn")
        open_dir_btn.clicked.connect(lambda: GameLauncher.open_game_folder(self.library_mgr.get_games_directory()))
        header_row.addWidget(open_dir_btn)

        main_layout.addLayout(header_row)

        # Sort Bar
        sort_bar = QHBoxLayout()
        sort_bar.setSpacing(10)

        sort_lbl = QLabel("Sortierung:")
        sort_lbl.setStyleSheet("font-weight: 600; color: #94a3b8; font-size: 12px;")
        sort_bar.addWidget(sort_lbl)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("🎮 Nach System / Plattform", "system")
        self.sort_combo.addItem("🔤 Name (A - Z)", "name_asc")
        self.sort_combo.addItem("⏱️ Zuletzt gespielt", "last_played")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.sort_combo.setMinimumWidth(210)
        sort_bar.addWidget(self.sort_combo)

        sort_bar.addStretch(1)
        main_layout.addLayout(sort_bar)

        # Scroll Area for List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.list_widget)

        main_layout.addWidget(scroll, 1)

        self.refresh_library()

    def _on_sort_changed(self, index: int):
        self.current_sort = self.sort_combo.currentData()
        self.refresh_library()

    def refresh_library(self):
        # Clear items
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        installed = list(self.library_mgr.installed_games.values())

        if not installed:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background-color: #131b2e; border: 1px dashed #334155; border-radius: 12px; padding: 40px;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            empty_icon = QLabel("🎮")
            empty_icon.setStyleSheet("font-size: 48px;")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_lbl = QLabel("Noch keine Spiele installiert")
            empty_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_lbl)

            desc_lbl = QLabel("Durchstöbere den Recomp- und Decomp-Katalog und lade dein erstes Spiel mit einem Klick herunter!")
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(desc_lbl)

            browse_btn = QPushButton("Katalog durchstöbern")
            browse_btn.setProperty("class", "primary-btn")
            browse_btn.setFixedWidth(200)
            browse_btn.clicked.connect(self.explore_requested.emit)
            empty_layout.addWidget(browse_btn, 0, Qt.AlignmentFlag.AlignCenter)

            self.list_layout.addWidget(empty_frame)
            self.subtitle.setText("0 Spiele installiert")
            return

        self.subtitle.setText(f"{len(installed)} Spiel(e) installiert")

        if self.current_sort == "system":
            self._render_grouped_by_system(installed)
        elif self.current_sort == "name_asc":
            installed.sort(key=lambda x: x.name.lower())
            for game in installed:
                proj = get_project_by_id(game.id)
                self.list_layout.addWidget(self._create_game_row(game, proj))
            self.list_layout.addStretch(1)
        elif self.current_sort == "last_played":
            installed.sort(key=lambda x: x.last_played or "", reverse=True)
            for game in installed:
                proj = get_project_by_id(game.id)
                self.list_layout.addWidget(self._create_game_row(game, proj))
            self.list_layout.addStretch(1)

    def _render_grouped_by_system(self, installed: List[InstalledGame]):
        """Render installed games grouped under system headers."""
        groups: Dict[str, List[tuple]] = {}
        for game in installed:
            proj = get_project_by_id(game.id)
            sys_name = proj.system_group if proj else "Weitere Systeme"
            groups.setdefault(sys_name, []).append((game, proj))

        ordered_keys = [s for s in SYSTEM_ORDER if s in groups]
        for k in groups.keys():
            if k not in ordered_keys:
                ordered_keys.append(k)

        for sys_name in ordered_keys:
            items = groups[sys_name]
            items.sort(key=lambda pair: pair[0].name.lower())

            # Header Frame
            header_frame = QFrame()
            header_frame.setStyleSheet("background-color: transparent; border: none; margin-top: 6px;")
            h_layout = QHBoxLayout(header_frame)
            h_layout.setContentsMargins(0, 0, 0, 4)
            h_layout.setSpacing(10)

            icon = SYSTEM_ICONS.get(sys_name, "🎮")
            sec_title = QLabel(f"{icon}  {sys_name}")
            sec_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
            h_layout.addWidget(sec_title)

            count_badge = QLabel(f"{len(items)} installiert")
            count_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 8px; border-radius: 6px;")
            h_layout.addWidget(count_badge)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #334155;")
            h_layout.addWidget(line, 1)

            self.list_layout.addWidget(header_frame)

            for game, proj in items:
                self.list_layout.addWidget(self._create_game_row(game, proj))

        self.list_layout.addStretch(1)

    def _create_game_row(self, game, proj) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #131b2e;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 10px 14px;
            }
            QFrame:hover {
                border-color: #334155;
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(16)

        # Icon
        icon_text = proj.icon_text if proj else "🎮"
        color = proj.color_accent if proj else "#38bdf8"
        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(f"""
            background-color: {color}22;
            border: 1px solid {color}55;
            border-radius: 8px;
            font-size: 22px;
            padding: 4px;
        """)
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Info column
        info_box = QVBoxLayout()
        info_box.setSpacing(2)

        name_lbl = QLabel(game.name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
        info_box.addWidget(name_lbl)

        plat_str = f" • {proj.original_platform}" if proj else ""
        meta_lbl = QLabel(f"Version: {game.version}{plat_str} | Zuletzt gespielt: {game.last_played or 'Nie'}")
        meta_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        info_box.addWidget(meta_lbl)

        layout.addLayout(info_box, 1)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)

        # Asset Helper Button
        if proj and proj.required_files:
            asset_btn = QPushButton("📁 ROMs/Dateien")
            asset_btn.setProperty("class", "secondary-btn")
            asset_btn.clicked.connect(lambda _, p=proj: self._open_asset_dialog(p))
            actions.addWidget(asset_btn)

        # Desktop Shortcut Button
        desktop_btn = QPushButton("📌 Menü-Eintrag")
        desktop_btn.setProperty("class", "secondary-btn")
        desktop_btn.clicked.connect(lambda _, p=proj: self._create_shortcut(p))
        actions.addWidget(desktop_btn)

        # Play Button
        play_btn = QPushButton("▶ Spielen")
        play_btn.setProperty("class", "success-btn")
        play_btn.clicked.connect(lambda _, gid=game.id: self.launch_requested.emit(gid))
        actions.addWidget(play_btn)

        # Delete Button
        del_btn = QPushButton("🗑️")
        del_btn.setToolTip("Deinstallieren")
        del_btn.setProperty("class", "danger-btn")
        del_btn.clicked.connect(lambda _, gid=game.id, name=game.name: self._confirm_uninstall(gid, name))
        actions.addWidget(del_btn)

        layout.addLayout(actions)
        return frame

    def _open_asset_dialog(self, project):
        dlg = AssetDialog(project, self.library_mgr, self)
        dlg.exec()

    def _create_shortcut(self, project):
        if not project:
            return
        ok = self.library_mgr.create_desktop_entry(project)
        if ok:
            QMessageBox.information(self, "Verknüpfung erstellt", f"Verknüpfung für '{project.name}' wurde im Linux-Anwendungsmenü angelegt!")
        else:
            QMessageBox.warning(self, "Fehler", "Konnte Desktop-Verknüpfung nicht erstellen.")

    def _confirm_uninstall(self, game_id: str, game_name: str):
        reply = QMessageBox.question(
            self,
            "Deinstallation bestätigen",
            f"Möchtest du '{game_name}' und alle zugehörigen Dateien wirklich deinstallieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.library_mgr.uninstall(game_id)
            self.refresh_library()
