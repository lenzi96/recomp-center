"""Game card widget for catalog and library grids."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...core.models import GameProject, ProjectType


class GameCard(QFrame):
    clicked = pyqtSignal(str)   # project_id
    install_clicked = pyqtSignal(str) # project_id
    launch_clicked = pyqtSignal(str)  # project_id
    compile_clicked = pyqtSignal(str) # project_id

    def __init__(self, project: GameProject, is_installed: bool = False, parent=None):
        super().__init__(parent)
        self.project = project
        self.is_installed = is_installed
        self.setProperty("class", "game-card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(170)

        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project.id)
        super().mousePressEvent(event)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header Row: Icon, Title, Platform & Type Badge
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        # Game Icon / Emoji Avatar
        icon_lbl = QLabel(self.project.icon_text)
        icon_lbl.setStyleSheet(f"""
            background-color: {self.project.color_accent}22;
            border: 1px solid {self.project.color_accent}55;
            border-radius: 10px;
            font-size: 24px;
            padding: 6px;
        """)
        icon_lbl.setFixedSize(46, 46)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(icon_lbl)

        # Title and author
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        name_lbl = QLabel(self.project.name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc;")
        title_box.addWidget(name_lbl)

        sub_lbl = QLabel(f"von {self.project.author} • {self.project.original_platform}")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(sub_lbl)

        header_row.addLayout(title_box, 1)

        # Badges
        badge_box = QVBoxLayout()
        badge_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        badge_box.setSpacing(4)

        type_badge = QLabel(self.project.project_type.value)
        type_badge.setProperty("class", "badge")
        if self.project.project_type == ProjectType.RECOMP:
            type_badge.setStyleSheet("background-color: #581c87; color: #d8b4fe; border-radius: 6px; padding: 3px 8px; font-weight: 600;")
        elif self.project.project_type == ProjectType.DECOMP_PORT:
            type_badge.setStyleSheet("background-color: #064e3b; color: #6ee7b7; border-radius: 6px; padding: 3px 8px; font-weight: 600;")
        else:
            type_badge.setStyleSheet("background-color: #78350f; color: #fcd34d; border-radius: 6px; padding: 3px 8px; font-weight: 600;")
        badge_box.addWidget(type_badge)

        if self.is_installed:
            inst_badge = QLabel("✓ Installiert")
            inst_badge.setStyleSheet("background-color: #065f46; color: #a7f3d0; border-radius: 6px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
            badge_box.addWidget(inst_badge)

        header_row.addLayout(badge_box)
        layout.addLayout(header_row)

        # Description
        desc_lbl = QLabel(self.project.short_desc)
        desc_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.3;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Footer Row: Actions
        footer = QHBoxLayout()
        footer.setSpacing(8)

        # Release hint
        if self.project.has_binary_releases:
            rel_hint = QLabel("📦 Linux Release verfügbar")
            rel_hint.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 500;")
        else:
            rel_hint = QLabel("⚙️ Source-Code Decomp")
            rel_hint.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: 500;")
        footer.addWidget(rel_hint)

        footer.addStretch(1)

        # Action button
        if self.is_installed:
            launch_btn = QPushButton("▶ Spielen")
            launch_btn.setProperty("class", "success-btn")
            launch_btn.clicked.connect(lambda: self.launch_clicked.emit(self.project.id))
            footer.addWidget(launch_btn)
        else:
            if self.project.has_binary_releases:
                dl_btn = QPushButton("⬇ Download")
                dl_btn.setProperty("class", "primary-btn")
                dl_btn.clicked.connect(lambda: self.install_clicked.emit(self.project.id))
                footer.addWidget(dl_btn)
            else:
                comp_btn = QPushButton("🔨 Kompilieren")
                comp_btn.setProperty("class", "primary-btn")
                comp_btn.setStyleSheet("background-color: #d97706; color: #ffffff;")
                comp_btn.clicked.connect(lambda: self.compile_clicked.emit(self.project.id))
                footer.addWidget(comp_btn)

        layout.addLayout(footer)
