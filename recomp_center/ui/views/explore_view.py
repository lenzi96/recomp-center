"""Explore / Catalog view for browsing all Recomps and Decomps with system sorting and grouping."""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QGridLayout, QFrame,
    QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...core.models import GameProject, ProjectType
from ...core.library import LibraryManager
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
        self.search_query = ""

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Recomp & Decomp Katalog")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #f8fafc;")
        title_box.addWidget(title)

        subtitle = QLabel("Entdecke native PC-Ports, statische Rekompilationen und Reverse-Engineering-Projekte.")
        subtitle.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box, 1)

        main_layout.addLayout(header_row)

        # Top Control Bar: Search & Sort Dropdown
        top_ctrl_bar = QHBoxLayout()
        top_ctrl_bar.setSpacing(12)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Nach Spiel, Entwickler oder System suchen...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        top_ctrl_bar.addWidget(self.search_input, 2)

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

        main_layout.addLayout(top_ctrl_bar)

        # Filter Bar: Project Types & System Pills
        filter_box = QVBoxLayout()
        filter_box.setSpacing(8)

        # Row 1: Type Tabs
        type_row = QHBoxLayout()
        type_row.setSpacing(6)

        type_lbl = QLabel("Typ:")
        type_lbl.setStyleSheet("font-weight: 600; color: #64748b; font-size: 11px; min-width: 48px;")
        type_row.addWidget(type_lbl)

        self.cat_btns = {}
        cats = [
            ("ALL", "Alle Typen"),
            ("RECOMP", "⚡ Recompilation"),
            ("DECOMP_PORT", "🎮 Spielbare Ports"),
            ("SOURCE_DECOMP", "📜 Source Decomps")
        ]
        for cat_id, cat_label in cats:
            btn = QPushButton(cat_label)
            btn.setCheckable(True)
            btn.setProperty("class", "secondary-btn")
            btn.clicked.connect(lambda checked, c=cat_id: self._on_category_clicked(c))
            type_row.addWidget(btn)
            self.cat_btns[cat_id] = btn

        self.cat_btns["ALL"].setChecked(True)
        self.cat_btns["ALL"].setStyleSheet("background-color: #0284c7; color: #ffffff; font-weight: bold;")
        type_row.addStretch(1)
        filter_box.addLayout(type_row)

        # Row 2: System Quick-Filter Pills
        sys_row = QHBoxLayout()
        sys_row.setSpacing(6)

        sys_lbl = QLabel("System:")
        sys_lbl.setStyleSheet("font-weight: 600; color: #64748b; font-size: 11px; min-width: 48px;")
        sys_row.addWidget(sys_lbl)

        self.system_btns = {}
        sys_options = [("ALL", "🎮 Alle Systeme")]
        for s in SYSTEM_ORDER:
            icon = SYSTEM_ICONS.get(s, "🎮")
            count = sum(1 for p in self.projects if p.system_group == s)
            if count > 0:
                sys_options.append((s, f"{icon} {s} ({count})"))

        for sys_id, sys_label in sys_options:
            sbtn = QPushButton(sys_label)
            sbtn.setCheckable(True)
            sbtn.setProperty("class", "secondary-btn")
            sbtn.setStyleSheet("font-size: 11px; padding: 4px 10px;")
            sbtn.clicked.connect(lambda checked, s=sys_id: self._on_system_clicked(s))
            sys_row.addWidget(sbtn)
            self.system_btns[sys_id] = sbtn

        self.system_btns["ALL"].setChecked(True)
        self.system_btns["ALL"].setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: bold; border-color: #38bdf8; font-size: 11px; padding: 4px 10px;")
        sys_row.addStretch(1)
        filter_box.addLayout(sys_row)

        main_layout.addLayout(filter_box)

        # Count Indicator
        self.count_lbl = QLabel(f"{len(self.projects)} Projekte verfügbar")
        self.count_lbl.setStyleSheet("color: #64748b; font-size: 12px; margin-top: 4px;")
        main_layout.addWidget(self.count_lbl)

        # Scroll Area for Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setSpacing(20)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.container_widget)

        main_layout.addWidget(scroll, 1)

        self.refresh_cards()

    def refresh_cards(self):
        # Clear container layout
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                # Clear sublayout
                subl = item.layout()
                while subl.count():
                    si = subl.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        filtered: List[GameProject] = []
        q = self.search_query.lower()

        for p in self.projects:
            # Type filter
            if self.current_filter_type == "RECOMP" and p.project_type != ProjectType.RECOMP:
                continue
            elif self.current_filter_type == "DECOMP_PORT" and p.project_type != ProjectType.DECOMP_PORT:
                continue
            elif self.current_filter_type == "SOURCE_DECOMP" and p.project_type != ProjectType.SOURCE_DECOMP:
                continue

            # System filter
            if self.current_system != "ALL" and p.system_group != self.current_system:
                continue

            # Search query
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
            empty_lbl = QLabel("Keine passenden Recomps oder Decomps gefunden.")
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px; text-align: center;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.container_layout.addWidget(empty_lbl)
            return

        # Handle Sorting & Display
        sort_mode = self.current_sort

        if sort_mode == "system":
            self._render_grouped_by_system(filtered)
        else:
            self._render_sorted_flat(filtered, sort_mode)

    def _render_grouped_by_system(self, projects: List[GameProject]):
        """Render cards separated by system section headers."""
        # Group projects by system
        system_groups: Dict[str, List[GameProject]] = {}
        for p in projects:
            grp = p.system_group
            system_groups.setdefault(grp, []).append(p)

        # Order systems by SYSTEM_ORDER
        ordered_keys = [s for s in SYSTEM_ORDER if s in system_groups]
        # Add any remaining keys
        for k in system_groups.keys():
            if k not in ordered_keys:
                ordered_keys.append(k)

        for sys_name in ordered_keys:
            projs_in_sys = system_groups[sys_name]
            # Sort within group by name
            projs_in_sys.sort(key=lambda x: x.name.lower())

            # Section Header Frame
            header_frame = QFrame()
            header_frame.setStyleSheet("background-color: transparent; border: none; margin-top: 6px;")
            h_layout = QHBoxLayout(header_frame)
            h_layout.setContentsMargins(0, 0, 0, 6)
            h_layout.setSpacing(10)

            icon = SYSTEM_ICONS.get(sys_name, "🎮")
            sec_title = QLabel(f"{icon}  {sys_name}")
            sec_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
            h_layout.addWidget(sec_title)

            count_badge = QLabel(f"{len(projs_in_sys)} Titel")
            count_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 8px; border-radius: 6px;")
            h_layout.addWidget(count_badge)

            # Divider line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #334155;")
            h_layout.addWidget(line, 1)

            self.container_layout.addWidget(header_frame)

            # Grid for this system
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(14)
            grid.setContentsMargins(0, 0, 0, 0)

            cols = 2
            for idx, proj in enumerate(projs_in_sys):
                row = idx // cols
                col = idx % cols
                card = GameCard(proj, is_installed=self.library_mgr.is_installed(proj.id))
                card.clicked.connect(self.project_selected.emit)
                card.install_clicked.connect(self.install_requested.emit)
                card.launch_clicked.connect(self.launch_requested.emit)
                card.compile_clicked.connect(self.compile_requested.emit)
                grid.addWidget(card, row, col)

            self.container_layout.addWidget(grid_widget)

        self.container_layout.addStretch(1)

    def _render_sorted_flat(self, projects: List[GameProject], sort_mode: str):
        """Render flat 2-column grid sorted by chosen attribute."""
        if sort_mode == "name_asc":
            projects.sort(key=lambda x: x.name.lower())
        elif sort_mode == "name_desc":
            projects.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_mode == "type":
            # Recomp first, then Decomp Port, then Source Decomp
            type_weight = {
                ProjectType.RECOMP: 1,
                ProjectType.DECOMP_PORT: 2,
                ProjectType.SOURCE_DECOMP: 3
            }
            projects.sort(key=lambda x: (type_weight.get(x.project_type, 4), x.name.lower()))
        elif sort_mode == "author_asc":
            projects.sort(key=lambda x: x.author.lower())

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        cols = 2
        for idx, proj in enumerate(projects):
            row = idx // cols
            col = idx % cols
            card = GameCard(proj, is_installed=self.library_mgr.is_installed(proj.id))
            card.clicked.connect(self.project_selected.emit)
            card.install_clicked.connect(self.install_requested.emit)
            card.launch_clicked.connect(self.launch_requested.emit)
            card.compile_clicked.connect(self.compile_requested.emit)
            grid.addWidget(card, row, col)

        self.container_layout.addWidget(grid_widget)
        self.container_layout.addStretch(1)

    def _on_search_changed(self, text: str):
        self.search_query = text.strip()
        self.refresh_cards()

    def _on_sort_changed(self, index: int):
        self.current_sort = self.sort_combo.currentData()
        self.refresh_cards()

    def _on_category_clicked(self, cat_id: str):
        self.current_filter_type = cat_id
        for cid, btn in self.cat_btns.items():
            if cid == cat_id:
                btn.setChecked(True)
                btn.setStyleSheet("background-color: #0284c7; color: #ffffff; font-weight: bold;")
            else:
                btn.setChecked(False)
                btn.setStyleSheet("")
        self.refresh_cards()

    def _on_system_clicked(self, sys_id: str):
        self.current_system = sys_id
        for sid, btn in self.system_btns.items():
            if sid == sys_id:
                btn.setChecked(True)
                btn.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: bold; border-color: #38bdf8; font-size: 11px; padding: 4px 10px;")
            else:
                btn.setChecked(False)
                btn.setStyleSheet("font-size: 11px; padding: 4px 10px;")
        self.refresh_cards()
