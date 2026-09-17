"""Game card widget for catalog and library grids with modern gaming aesthetics."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...core.models import GameProject, ProjectType


class GameCard(QFrame):
    clicked = pyqtSignal(str)          # project_id
    install_clicked = pyqtSignal(str)  # project_id
    launch_clicked = pyqtSignal(str)   # project_id
    compile_clicked = pyqtSignal(str)  # project_id
    open_folder_clicked = pyqtSignal(str) # project_id
    uninstall_clicked = pyqtSignal(str)   # project_id

    def __init__(self, project: GameProject, is_installed: bool = False, parent=None):
        super().__init__(parent)
        self.project = project
        self.is_installed = is_installed
        self.setProperty("class", "game-card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(185)

        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project.id)
        super().mousePressEvent(event)

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top Accent Color Bar (glow header strip)
        accent = self.project.color_accent or "#38bdf8"
        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent}, stop:0.7 {accent}88, stop:1 transparent);
            border-top-left-radius: 11px;
            border-top-right-radius: 11px;
        """)
        root_layout.addWidget(accent_bar)

        # Inner Content Layout
        content_box = QVBoxLayout()
        content_box.setContentsMargins(16, 12, 16, 14)
        content_box.setSpacing(10)
        root_layout.addLayout(content_box)

        # Header Row: Icon, Title, Badges
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        # Game Icon / Avatar with colored ring
        icon_lbl = QLabel(self.project.icon_text)
        icon_lbl.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent}33, stop:1 #0c1220);
            border: 1.5px solid {accent}77;
            border-radius: 12px;
            font-size: 26px;
        """)
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(icon_lbl)

        # Title and author
        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        name_lbl = QLabel(self.project.name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff; letter-spacing: 0.2px;")
        title_box.addWidget(name_lbl)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)
        sub_lbl = QLabel(f"von <b style='color: #cbd5e1;'>{self.project.author}</b>")
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        meta_row.addWidget(sub_lbl)

        # Platform pill
        plat_pill = QLabel(self.project.original_platform)
        plat_pill.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.06);
            color: #94a3b8;
            font-size: 10px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid #1e293b;
        """)
        meta_row.addWidget(plat_pill)
        meta_row.addStretch(1)
        title_box.addLayout(meta_row)

        header_row.addLayout(title_box, 1)

        # Badges Column
        badge_box = QVBoxLayout()
        badge_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        badge_box.setSpacing(5)

        type_badge = QLabel(self.project.project_type.value)
        type_badge.setProperty("class", "badge")
        if self.project.project_type == ProjectType.RECOMP:
            type_badge.setStyleSheet("background-color: #581c87; color: #e9d5ff; border: 1px solid #7e22ce; border-radius: 6px; padding: 3px 8px; font-weight: 700; font-size: 10px;")
        elif self.project.project_type == ProjectType.DECOMP_PORT:
            type_badge.setStyleSheet("background-color: #064e3b; color: #a7f3d0; border: 1px solid #059669; border-radius: 6px; padding: 3px 8px; font-weight: 700; font-size: 10px;")
        else:
            type_badge.setStyleSheet("background-color: #78350f; color: #fde68a; border: 1px solid #b45309; border-radius: 6px; padding: 3px 8px; font-weight: 700; font-size: 10px;")
        badge_box.addWidget(type_badge)

        if self.is_installed:
            inst_badge = QLabel("✓ Installiert")
            inst_badge.setStyleSheet("background-color: #047857; color: #ffffff; border-radius: 6px; padding: 2px 7px; font-size: 10px; font-weight: 800;")
            badge_box.addWidget(inst_badge)

        header_row.addLayout(badge_box)
        content_box.addLayout(header_row)

        # Short Description
        desc_lbl = QLabel(self.project.short_desc)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.35;")
        desc_lbl.setWordWrap(True)
        content_box.addWidget(desc_lbl)

        content_box.addStretch(1)

        # Footer Row: Status & Actions
        footer = QHBoxLayout()
        footer.setSpacing(8)

        # Release badge / hint
        if self.project.has_binary_releases:
            rel_hint = QLabel("📦 Linux Release")
            rel_hint.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600;")
        else:
            rel_hint = QLabel("⚙️ Source Decomp")
            rel_hint.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 600;")
        footer.addWidget(rel_hint)

        footer.addStretch(1)

        # Action buttons
        if self.is_installed:
            launch_btn = QPushButton("▶ Spielen")
            launch_btn.setProperty("class", "success-btn")
            launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            launch_btn.clicked.connect(lambda: self.launch_clicked.emit(self.project.id))
            footer.addWidget(launch_btn)

            # Extra options menu button
            opt_btn = QPushButton("•••")
            opt_btn.setProperty("class", "secondary-btn")
            opt_btn.setFixedWidth(36)
            opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            opt_btn.setToolTip("Weitere Aktionen")
            opt_btn.clicked.connect(lambda: self._show_context_menu(opt_btn))
            footer.addWidget(opt_btn)
        else:
            if self.project.has_binary_releases:
                dl_btn = QPushButton("⬇ Download")
                dl_btn.setProperty("class", "primary-btn")
                dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                dl_btn.clicked.connect(lambda: self.install_clicked.emit(self.project.id))
                footer.addWidget(dl_btn)
            else:
                comp_btn = QPushButton("🔨 Kompilieren")
                comp_btn.setProperty("class", "primary-btn")
                comp_btn.setStyleSheet("""
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b);
                    color: #ffffff;
                    border: 1px solid #fbbf24;
                """)
                comp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                comp_btn.clicked.connect(lambda: self.compile_clicked.emit(self.project.id))
                footer.addWidget(comp_btn)

        content_box.addLayout(footer)

    def _show_context_menu(self, source_btn: QPushButton):
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

        act_folder = menu.addAction("📁 Ordner im Dateimanager öffnen")
        act_details = menu.addAction("🔍 Details & Spieldaten anzeigen")
        menu.addSeparator()
        act_uninstall = menu.addAction("🗑️ Deinstallieren")

        action = menu.exec(source_btn.mapToGlobal(source_btn.rect().bottomLeft()))
        if action == act_folder:
            self.open_folder_clicked.emit(self.project.id)
        elif action == act_details:
            self.clicked.emit(self.project.id)
        elif action == act_uninstall:
            self.uninstall_clicked.emit(self.project.id)

