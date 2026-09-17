"""Library view for managing installed Recomp/Decomp games with system grouping, stats, and search."""

import os
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QComboBox, QLineEdit, QMenu
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
        self.search_query = ""
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title & Global Actions
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Meine Bibliothek")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 0.3px;")
        title_box.addWidget(title)

        self.subtitle = QLabel("Installierte Recomp- & Decomp-Ports auf diesem PC.")
        self.subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(self.subtitle)
        header_row.addLayout(title_box, 1)

        open_dir_btn = QPushButton("📁 Spiele-Ordner öffnen")
        open_dir_btn.setProperty("class", "secondary-btn")
        open_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_dir_btn.clicked.connect(lambda: GameLauncher.open_game_folder(self.library_mgr.get_games_directory()))
        header_row.addWidget(open_dir_btn)

        main_layout.addLayout(header_row)

        # Stats Summary Bar (Glass Cards)
        self.stats_bar = QHBoxLayout()
        self.stats_bar.setSpacing(12)

        self.stat_count_card = self._create_stat_card("🎮", "0", "Installierte Spiele")
        self.stat_disk_card = self._create_stat_card("💾", "0 MB", "Speicherplatz")
        self.stat_ready_card = self._create_stat_card("⚡", "0", "Startbereit")

        self.stats_bar.addWidget(self.stat_count_card)
        self.stats_bar.addWidget(self.stat_disk_card)
        self.stats_bar.addWidget(self.stat_ready_card)
        self.stats_bar.addStretch(1)

        main_layout.addLayout(self.stats_bar)

        # Filter & Search Controls
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Installierte Spiele durchsuchen...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        ctrl_bar.addWidget(self.search_input, 2)

        sort_lbl = QLabel("Sortierung:")
        sort_lbl.setStyleSheet("font-weight: 600; color: #94a3b8; font-size: 12px;")
        ctrl_bar.addWidget(sort_lbl)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("🎮 Nach System / Plattform", "system")
        self.sort_combo.addItem("🔤 Name (A - Z)", "name_asc")
        self.sort_combo.addItem("⏱️ Zuletzt gespielt", "last_played")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.sort_combo.setMinimumWidth(210)
        ctrl_bar.addWidget(self.sort_combo)

        main_layout.addLayout(ctrl_bar)

        # Scroll Area for List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.list_widget)

        main_layout.addWidget(scroll, 1)

        self.refresh_library()

    def _create_stat_card(self, icon: str, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 6px 14px;
            }
        """)
        c_layout = QHBoxLayout(card)
        c_layout.setContentsMargins(8, 6, 8, 6)
        c_layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        c_layout.addWidget(icon_lbl)

        v_box = QVBoxLayout()
        v_box.setSpacing(1)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("stat_value")
        val_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #ffffff;")
        v_box.addWidget(val_lbl)

        desc_lbl = QLabel(label)
        desc_lbl.setStyleSheet("font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase;")
        v_box.addWidget(desc_lbl)

        c_layout.addLayout(v_box)
        return card

    def _update_stats(self, installed_list: List[InstalledGame]):
        count = len(installed_list)
        self.stat_count_card.findChild(QLabel, "stat_value").setText(str(count))

        # Calculate disk usage
        total_bytes = 0
        for game in installed_list:
            if game.install_path and os.path.exists(game.install_path):
                for root, dirs, files in os.walk(game.install_path):
                    for f in files:
                        try:
                            total_bytes += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass

        if total_bytes > 1024 * 1024 * 1024:
            usage_str = f"{total_bytes / (1024*1024*1024):.1f} GB"
        elif total_bytes > 1024 * 1024:
            usage_str = f"{total_bytes / (1024*1024):.1f} MB"
        else:
            usage_str = f"{total_bytes / 1024:.0f} KB"
        self.stat_disk_card.findChild(QLabel, "stat_value").setText(usage_str)

        # Count ready (assets verified)
        ready_count = 0
        for game in installed_list:
            proj = get_project_by_id(game.id)
            if proj and proj.required_files:
                has_assets, _ = self.library_mgr.check_game_assets(proj)
                if has_assets:
                    ready_count += 1
            else:
                ready_count += 1
        self.stat_ready_card.findChild(QLabel, "stat_value").setText(str(ready_count))

    def _on_search_changed(self, text: str):
        self.search_query = text.strip().lower()
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

        all_installed = list(self.library_mgr.installed_games.values())
        self._update_stats(all_installed)

        if not all_installed:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background-color: #111726; border: 1px dashed #334155; border-radius: 12px; padding: 40px;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            empty_icon = QLabel("🎮")
            empty_icon.setStyleSheet("font-size: 48px;")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_lbl = QLabel("Noch keine Spiele installiert")
            empty_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_lbl)

            desc_lbl = QLabel("Durchstöbere den Recomp- und Decomp-Katalog und lade dein erstes Spiel mit einem Klick herunter!")
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(desc_lbl)

            browse_btn = QPushButton("Katalog durchstöbern")
            browse_btn.setProperty("class", "primary-btn")
            browse_btn.setFixedWidth(200)
            browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            browse_btn.clicked.connect(self.explore_requested.emit)
            empty_layout.addWidget(browse_btn, 0, Qt.AlignmentFlag.AlignCenter)

            self.list_layout.addWidget(empty_frame)
            self.subtitle.setText("0 Spiele installiert")
            return

        # Filter by search
        installed = []
        for g in all_installed:
            if self.search_query:
                if self.search_query not in g.name.lower() and self.search_query not in g.id.lower():
                    continue
            installed.append(g)

        self.subtitle.setText(f"{len(installed)} Spiel(e) installiert")

        if not installed:
            no_match = QLabel(f"Kein installiertes Spiel gefunden für '{self.search_query}'.")
            no_match.setStyleSheet("color: #94a3b8; font-size: 13px; padding: 30px; text-align: center;")
            no_match.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(no_match)
            return

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

            header_frame = QFrame()
            header_frame.setStyleSheet("background-color: transparent; border: none; margin-top: 8px;")
            h_layout = QHBoxLayout(header_frame)
            h_layout.setContentsMargins(0, 0, 0, 4)
            h_layout.setSpacing(10)

            icon = SYSTEM_ICONS.get(sys_name, "🎮")
            sec_title = QLabel(f"{icon}  {sys_name}")
            sec_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #f8fafc;")
            h_layout.addWidget(sec_title)

            count_badge = QLabel(f"{len(items)} installiert")
            count_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 600;")
            h_layout.addWidget(count_badge)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #1e293b;")
            h_layout.addWidget(line, 1)

            self.list_layout.addWidget(header_frame)

            for game, proj in items:
                self.list_layout.addWidget(self._create_game_row(game, proj))

        self.list_layout.addStretch(1)

    def _create_game_row(self, game, proj) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #111726;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 10px 14px;
            }
            QFrame:hover {
                border-color: #38bdf8;
                background-color: #151d30;
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Icon with colored border
        icon_text = proj.icon_text if proj else "🎮"
        color = proj.color_accent if proj else "#38bdf8"
        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(f"""
            background: {color}22;
            border: 1.5px solid {color}66;
            border-radius: 10px;
            font-size: 24px;
        """)
        icon_lbl.setFixedSize(46, 46)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Info column
        info_box = QVBoxLayout()
        info_box.setSpacing(3)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_lbl = QLabel(game.name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff;")
        name_row.addWidget(name_lbl)

        # Readiness pill
        if proj and proj.required_files:
            has_assets, _ = self.library_mgr.check_game_assets(proj)
            if has_assets:
                ready_lbl = QLabel("✓ Startbereit")
                ready_lbl.setStyleSheet("background-color: #047857; color: #a7f3d0; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 5px;")
            else:
                ready_lbl = QLabel("⚠️ ROMs fehlen")
                ready_lbl.setStyleSheet("background-color: #78350f; color: #fde68a; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 5px;")
            name_row.addWidget(ready_lbl)

        name_row.addStretch(1)
        info_box.addLayout(name_row)

        plat_str = f" • {proj.original_platform}" if proj else ""
        meta_lbl = QLabel(f"Version: <b style='color: #cbd5e1;'>{game.version}</b>{plat_str} | Zuletzt gespielt: <b style='color: #cbd5e1;'>{game.last_played or 'Nie'}</b>")
        meta_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        info_box.addWidget(meta_lbl)

        layout.addLayout(info_box, 1)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)

        # Play Button
        play_btn = QPushButton("▶ Spielen")
        play_btn.setProperty("class", "success-btn")
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(lambda _, gid=game.id: self.launch_requested.emit(gid))
        actions.addWidget(play_btn)

        # Open Folder
        folder_btn = QPushButton("📁 Ordner")
        folder_btn.setProperty("class", "secondary-btn")
        folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        folder_btn.clicked.connect(lambda _, p=game.install_path: GameLauncher.open_game_folder(p))
        actions.addWidget(folder_btn)

        # Extra Options Dropdown
        more_btn = QPushButton("•••")
        more_btn.setProperty("class", "secondary-btn")
        more_btn.setFixedWidth(36)
        more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        more_btn.clicked.connect(lambda _, b=more_btn, g=game, p=proj: self._show_game_menu(b, g, p))
        actions.addWidget(more_btn)

        layout.addLayout(actions)
        return frame

    def _show_game_menu(self, btn: QPushButton, game: InstalledGame, project: GameProject):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #111726;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)

        if project and project.required_files:
            act_assets = menu.addAction("💾 ROMs / Spieldateien verwalten...")
        else:
            act_assets = None

        act_desktop = menu.addAction("📌 Desktop-Verknüpfung erstellen")
        menu.addSeparator()
        act_uninstall = menu.addAction("🗑️ Spiel deinstallieren")

        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if action == act_assets and project:
            self._open_asset_dialog(project)
        elif action == act_desktop and project:
            self._create_shortcut(project)
        elif action == act_uninstall:
            self._confirm_uninstall(game.id, game.name)

    def _open_asset_dialog(self, project):
        dlg = AssetDialog(project, self.library_mgr, self)
        dlg.exec()
        self.refresh_library()

    def _create_shortcut(self, project):
        if not project:
            return
        ok = self.library_mgr.create_desktop_entry(project)
        if ok:
            QMessageBox.information(self, "Verknüpfung erstellt", f"Verknüpfung für '{project.name}' wurde erfolgreich im Anwendungsmenü erstellt!")
        else:
            QMessageBox.warning(self, "Fehler", "Konnte Desktop-Verknüpfung nicht erstellen.")

    def _confirm_uninstall(self, game_id: str, game_name: str):
        reply = QMessageBox.question(
            self,
            "Deinstallation bestätigen",
            f"Möchtest du '{game_name}' und alle zugehörigen Spieldateien wirklich deinstallieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.library_mgr.uninstall(game_id)
            self.refresh_library()

