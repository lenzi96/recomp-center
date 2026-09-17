"""Explore / Catalog view for browsing all Recomps and Decomps with system sorting, grouping, and view modes."""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QGridLayout, QFrame,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...core.models import GameProject, ProjectType
from ...core.library import LibraryManager
from ...core.launcher import GameLauncher
from ...data.catalog import SYSTEM_ORDER, SYSTEM_ICONS, get_system_group
from ..widgets.game_card import GameCard


class ExploreView(QWidget):
    project_selected = pyqtSignal(str)
    install_requested = pyqtSignal(str)
    launch_requested = pyqtSignal(str)
    compile_requested = pyqtSignal(str)

    def __init__(self, projects: list[GameProject], library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.projects = projects
        self.library_mgr = library_mgr
        self.current_filter_type = "ALL"
        self.current_system = "ALL"
        self.current_sort = "system"  # Default: sort by system
        self.current_view_mode = "grid"  # 'grid' or 'list'
        self.search_query = ""

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Title Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Recomp & Decomp Katalog")
        title.setStyleSheet("font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 0.3px;")
        title_box.addWidget(title)

        subtitle = QLabel("Entdecke native PC-Ports, statische Rekompilationen und Reverse-Engineering-Projekte.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box, 1)

        # View Switcher (Grid vs List)
        view_toggle_frame = QFrame()
        view_toggle_frame.setStyleSheet("background-color: #111726; border: 1px solid #1e293b; border-radius: 8px;")
        v_layout = QHBoxLayout(view_toggle_frame)
        v_layout.setContentsMargins(3, 3, 3, 3)
        v_layout.setSpacing(2)

        self.btn_grid_view = QPushButton("⊞ Raster")
        self.btn_grid_view.setProperty("class", "pill-btn")
        self.btn_grid_view.setCheckable(True)
        self.btn_grid_view.setChecked(True)
        self.btn_grid_view.clicked.connect(lambda: self._set_view_mode("grid"))
        v_layout.addWidget(self.btn_grid_view)

        self.btn_list_view = QPushButton("☰ Liste")
        self.btn_list_view.setProperty("class", "pill-btn")
        self.btn_list_view.setCheckable(True)
        self.btn_list_view.clicked.connect(lambda: self._set_view_mode("list"))
        v_layout.addWidget(self.btn_list_view)

        header_row.addWidget(view_toggle_frame)
        main_layout.addLayout(header_row)

        # Control Bar: Search Input & Sort Dropdown
        top_ctrl_bar = QHBoxLayout()
        top_ctrl_bar.setSpacing(12)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Spiel, Entwickler, Plattform oder Genre suchen...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_ctrl_bar.addWidget(self.search_input, 3)

        # Sort Label & Combobox
        sort_lbl = QLabel("Sortierung:")
        sort_lbl.setStyleSheet("font-weight: 600; color: #94a3b8; font-size: 12px;")
        top_ctrl_bar.addWidget(sort_lbl)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("🎮 Nach System / Plattform", "system")
        self.sort_combo.addItem("🔤 Name (A - Z)", "name_asc")
        self.sort_combo.addItem("🔤 Name (Z - A)", "name_desc")
        self.sort_combo.addItem("⚡ Projekt-Typ (Recomp zuerst)", "type")
        self.sort_combo.addItem("👤 Entwickler (A - Z)", "author_asc")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.sort_combo.setMinimumWidth(210)
        top_ctrl_bar.addWidget(self.sort_combo)

        # Reset Filter Button
        self.btn_reset_filters = QPushButton("✕ Filter zurücksetzen")
        self.btn_reset_filters.setProperty("class", "secondary-btn")
        self.btn_reset_filters.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_filters.setVisible(False)
        self.btn_reset_filters.clicked.connect(self._reset_all_filters)
        top_ctrl_bar.addWidget(self.btn_reset_filters)

        main_layout.addLayout(top_ctrl_bar)

        # Filter Box: Categories & Systems
        filter_box = QVBoxLayout()
        filter_box.setSpacing(8)

        # Row 1: Type Tabs
        type_row = QHBoxLayout()
        type_row.setSpacing(6)

        type_lbl = QLabel("Kategorie:")
        type_lbl.setStyleSheet("font-weight: 700; color: #64748b; font-size: 11px; min-width: 65px;")
        type_row.addWidget(type_lbl)

        self.cat_btns = {}
        cats = [
            ("ALL", "✨ Alle Typen"),
            ("RECOMP", "⚡ Recompilation"),
            ("DECOMP_PORT", "🎮 Spielbare Ports"),
            ("SOURCE_DECOMP", "📜 Source Decomps")
        ]
        for cat_id, cat_label in cats:
            btn = QPushButton(cat_label)
            btn.setCheckable(True)
            btn.setProperty("class", "pill-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=cat_id: self._on_category_clicked(c))
            type_row.addWidget(btn)
            self.cat_btns[cat_id] = btn

        self.cat_btns["ALL"].setChecked(True)
        type_row.addStretch(1)
        filter_box.addLayout(type_row)

        # Row 2: System Quick-Filter Pills
        sys_row = QHBoxLayout()
        sys_row.setSpacing(6)

        sys_lbl = QLabel("Plattform:")
        sys_lbl.setStyleSheet("font-weight: 700; color: #64748b; font-size: 11px; min-width: 65px;")
        sys_row.addWidget(sys_lbl)

        self.system_btns = {}
        sys_options = [("ALL", "🎮 Alle Plattformen")]
        for s in SYSTEM_ORDER:
            icon = SYSTEM_ICONS.get(s, "🎮")
            count = sum(1 for p in self.projects if p.system_group == s)
            if count > 0:
                sys_options.append((s, f"{icon} {s} ({count})"))

        for sys_id, sys_label in sys_options:
            sbtn = QPushButton(sys_label)
            sbtn.setCheckable(True)
            sbtn.setProperty("class", "pill-btn")
            sbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            sbtn.clicked.connect(lambda checked, s=sys_id: self._on_system_clicked(s))
            sys_row.addWidget(sbtn)
            self.system_btns[sys_id] = sbtn

        self.system_btns["ALL"].setChecked(True)
        sys_row.addStretch(1)
        filter_box.addLayout(sys_row)

        main_layout.addLayout(filter_box)

        # Live Results Count Indicator
        self.count_lbl = QLabel(f"{len(self.projects)} Projekte verfügbar")
        self.count_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600; margin-top: 2px;")
        main_layout.addWidget(self.count_lbl)

        # Scroll Area for Cards / List Items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setSpacing(16)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.container_widget)

        main_layout.addWidget(scroll, 1)

        self.refresh_cards()

    def _set_view_mode(self, mode: str):
        self.current_view_mode = mode
        self.btn_grid_view.setChecked(mode == "grid")
        self.btn_list_view.setChecked(mode == "list")
        self.refresh_cards()

    def _reset_all_filters(self):
        self.search_input.clear()
        self.search_query = ""
        self.current_filter_type = "ALL"
        for cid, btn in self.cat_btns.items():
            btn.setChecked(cid == "ALL")
        self.current_system = "ALL"
        for sid, btn in self.system_btns.items():
            btn.setChecked(sid == "ALL")
        self.btn_reset_filters.setVisible(False)
        self.refresh_cards()

    def refresh_cards(self):
        # Clear container layout
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                subl = item.layout()
                while subl.count():
                    si = subl.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        filtered: List[GameProject] = []
        q = self.search_query.lower()
        has_active_filter = bool(q or self.current_filter_type != "ALL" or self.current_system != "ALL")
        self.btn_reset_filters.setVisible(has_active_filter)

        for p in self.projects:
            if self.current_filter_type == "RECOMP" and p.project_type != ProjectType.RECOMP:
                continue
            elif self.current_filter_type == "DECOMP_PORT" and p.project_type != ProjectType.DECOMP_PORT:
                continue
            elif self.current_filter_type == "SOURCE_DECOMP" and p.project_type != ProjectType.SOURCE_DECOMP:
                continue

            if self.current_system != "ALL" and p.system_group != self.current_system:
                continue

            if q:
                match_name = q in p.name.lower()
                match_author = q in p.author.lower()
                match_plat = q in p.original_platform.lower()
                match_sys = q in p.system_group.lower()
                match_desc = q in p.short_desc.lower()
                if not (match_name or match_author or match_plat or match_sys or match_desc):
                    continue

            filtered.append(p)

        self.count_lbl.setText(f"{len(filtered)} von {len(self.projects)} Projekten angezeigt")

        if not filtered:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background-color: #111726; border: 1px dashed #334155; border-radius: 12px; padding: 40px;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            empty_icon = QLabel("🔍")
            empty_icon.setStyleSheet("font-size: 40px;")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_lbl = QLabel("Keine passenden Recomps oder Decomps gefunden")
            empty_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_lbl)

            desc_lbl = QLabel("Versuche einen anderen Suchbegriff oder setze die Filter zurück.")
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(desc_lbl)

            btn_reset = QPushButton("Filter zurücksetzen")
            btn_reset.setProperty("class", "primary-btn")
            btn_reset.setFixedWidth(180)
            btn_reset.clicked.connect(self._reset_all_filters)
            empty_layout.addWidget(btn_reset, 0, Qt.AlignmentFlag.AlignCenter)

            self.container_layout.addWidget(empty_frame)
            return

        sort_mode = self.current_sort

        if self.current_view_mode == "list":
            self._render_list_view(filtered, sort_mode)
        else:
            if sort_mode == "system":
                self._render_grouped_by_system(filtered)
            else:
                self._render_sorted_flat(filtered, sort_mode)

    def _render_grouped_by_system(self, projects: List[GameProject]):
        system_groups: Dict[str, List[GameProject]] = {}
        for p in projects:
            grp = p.system_group
            system_groups.setdefault(grp, []).append(p)

        ordered_keys = [s for s in SYSTEM_ORDER if s in system_groups]
        for k in system_groups.keys():
            if k not in ordered_keys:
                ordered_keys.append(k)

        for sys_name in ordered_keys:
            projs_in_sys = system_groups[sys_name]
            projs_in_sys.sort(key=lambda x: x.name.lower())

            header_frame = QFrame()
            header_frame.setStyleSheet("background-color: transparent; border: none; margin-top: 6px;")
            h_layout = QHBoxLayout(header_frame)
            h_layout.setContentsMargins(0, 0, 0, 6)
            h_layout.setSpacing(10)

            icon = SYSTEM_ICONS.get(sys_name, "🎮")
            sec_title = QLabel(f"{icon}  {sys_name}")
            sec_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #f8fafc;")
            h_layout.addWidget(sec_title)

            count_badge = QLabel(f"{len(projs_in_sys)} Titel")
            count_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 600;")
            h_layout.addWidget(count_badge)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #1e293b;")
            h_layout.addWidget(line, 1)

            self.container_layout.addWidget(header_frame)

            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(14)
            grid.setContentsMargins(0, 0, 0, 0)

            cols = 2
            for idx, proj in enumerate(projs_in_sys):
                row = idx // cols
                col = idx % cols
                card = self._create_card(proj)
                grid.addWidget(card, row, col)

            self.container_layout.addWidget(grid_widget)

        self.container_layout.addStretch(1)

    def _render_sorted_flat(self, projects: List[GameProject], sort_mode: str):
        self._sort_projects_list(projects, sort_mode)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        cols = 2
        for idx, proj in enumerate(projects):
            row = idx // cols
            col = idx % cols
            card = self._create_card(proj)
            grid.addWidget(card, row, col)

        self.container_layout.addWidget(grid_widget)
        self.container_layout.addStretch(1)

    def _render_list_view(self, projects: List[GameProject], sort_mode: str):
        """Render a compact table/list of games."""
        self._sort_projects_list(projects, sort_mode)

        for proj in projects:
            row_card = QFrame()
            row_card.setProperty("class", "game-card")
            row_card.setCursor(Qt.CursorShape.PointingHandCursor)
            row_layout = QHBoxLayout(row_card)
            row_layout.setContentsMargins(14, 10, 14, 10)
            row_layout.setSpacing(12)

            # Icon
            accent = proj.color_accent or "#38bdf8"
            icon_lbl = QLabel(proj.icon_text)
            icon_lbl.setStyleSheet(f"""
                background: {accent}22;
                border: 1px solid {accent}66;
                border-radius: 8px;
                font-size: 20px;
            """)
            icon_lbl.setFixedSize(38, 38)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(icon_lbl)

            # Name & author
            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            name_lbl = QLabel(proj.name)
            name_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
            info_col.addWidget(name_lbl)

            sub_lbl = QLabel(f"von {proj.author} • {proj.original_platform}")
            sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
            info_col.addWidget(sub_lbl)
            row_layout.addLayout(info_col, 2)

            # Type badge
            type_badge = QLabel(proj.project_type.value)
            type_badge.setStyleSheet("background-color: #1e293b; color: #cbd5e1; font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 6px;")
            row_layout.addWidget(type_badge)

            # Installed badge
            is_inst = self.library_mgr.is_installed(proj.id)
            if is_inst:
                inst_lbl = QLabel("✓ Installiert")
                inst_lbl.setStyleSheet("background-color: #047857; color: #ffffff; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 5px;")
                row_layout.addWidget(inst_lbl)

            # Action button
            if is_inst:
                btn = QPushButton("▶ Spielen")
                btn.setProperty("class", "success-btn")
                btn.clicked.connect(lambda ch, pid=proj.id: self.launch_requested.emit(pid))
            elif proj.has_binary_releases:
                btn = QPushButton("⬇ Download")
                btn.setProperty("class", "primary-btn")
                btn.clicked.connect(lambda ch, pid=proj.id: self.install_requested.emit(pid))
            else:
                btn = QPushButton("🔨 Build")
                btn.setProperty("class", "secondary-btn")
                btn.clicked.connect(lambda ch, pid=proj.id: self.compile_requested.emit(pid))

            btn.setFixedHeight(32)
            row_layout.addWidget(btn)

            # Click row for details
            row_card.mousePressEvent = lambda ev, pid=proj.id: self.project_selected.emit(pid)

            self.container_layout.addWidget(row_card)

        self.container_layout.addStretch(1)

    def _sort_projects_list(self, projects: List[GameProject], sort_mode: str):
        if sort_mode == "name_asc":
            projects.sort(key=lambda x: x.name.lower())
        elif sort_mode == "name_desc":
            projects.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_mode == "type":
            type_weight = {
                ProjectType.RECOMP: 1,
                ProjectType.DECOMP_PORT: 2,
                ProjectType.SOURCE_DECOMP: 3
            }
            projects.sort(key=lambda x: (type_weight.get(x.project_type, 4), x.name.lower()))
        elif sort_mode == "author_asc":
            projects.sort(key=lambda x: x.author.lower())

    def _create_card(self, proj: GameProject) -> GameCard:
        card = GameCard(proj, is_installed=self.library_mgr.is_installed(proj.id))
        card.clicked.connect(self.project_selected.emit)
        card.install_requested = card.install_clicked
        card.install_clicked.connect(self.install_requested.emit)
        card.launch_clicked.connect(self.launch_requested.emit)
        card.compile_clicked.connect(self.compile_requested.emit)
        card.open_folder_clicked.connect(self._open_game_folder)
        card.uninstall_clicked.connect(self._uninstall_game)
        return card

    def _open_game_folder(self, project_id: str):
        installed = self.library_mgr.get_installed(project_id)
        if installed and installed.install_path:
            GameLauncher.open_game_folder(installed.install_path)

    def _uninstall_game(self, project_id: str):
        proj = [p for p in self.projects if p.id == project_id]
        name = proj[0].name if proj else project_id
        reply = QMessageBox.question(
            self,
            "Spiel deinstallieren",
            f"Möchtest du '{name}' wirklich deinstallieren?\nAlle installierten Spieldateien in diesem Verzeichnis werden entfernt.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.library_mgr.uninstall(project_id)
            self.refresh_cards()

    def _on_search_changed(self, text: str):
        self.search_query = text.strip()
        self.refresh_cards()

    def _on_sort_changed(self, index: int):
        self.current_sort = self.sort_combo.currentData()
        self.refresh_cards()

    def _on_category_clicked(self, cat_id: str):
        self.current_filter_type = cat_id
        for cid, btn in self.cat_btns.items():
            btn.setChecked(cid == cat_id)
        self.refresh_cards()

    def _on_system_clicked(self, sys_id: str):
        self.current_system = sys_id
        for sid, btn in self.system_btns.items():
            btn.setChecked(sid == sys_id)
        self.refresh_cards()

