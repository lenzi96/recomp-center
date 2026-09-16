"""Data models for Recomp Center."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class ProjectType(str, Enum):
    RECOMP = "Recompilation"
    DECOMP_PORT = "Decomp Port"
    SOURCE_DECOMP = "Source Decomp"


@dataclass
class GameProject:
    id: str
    name: str
    short_desc: str
    author: str
    repo: str  # Format: "owner/repo"
    project_type: ProjectType
    original_platform: str
    website_url: str = ""
    has_binary_releases: bool = True
    linux_asset_patterns: List[str] = field(default_factory=lambda: ["linux", "x86_64", "appimage", "tar.gz"])
    executable_hints: List[str] = field(default_factory=list)
    required_assets_desc: str = ""
    required_files: List[str] = field(default_factory=list)
    asset_target_subpath: str = ""
    full_desc: str = ""
    color_accent: str = "#38bdf8"
    icon_text: str = "🎮"
    can_compile: bool = True
    build_commands: List[str] = field(default_factory=list)
    build_dependencies: List[str] = field(default_factory=list)
    build_notes: str = ""

    @property
    def github_url(self) -> str:
        if self.repo:
            return f"https://github.com/{self.repo}"
        return self.website_url

    @property
    def system_group(self) -> str:
        plat = self.original_platform.lower()
        if "nintendo 64" in plat or "n64" in plat:
            return "Nintendo 64"
        elif "xbox" in plat or "x360" in plat:
            return "Xbox & Xbox 360"
        elif "playstation 2" in plat or "ps2" in plat:
            return "PlayStation 2"
        elif "playstation" in plat or "ps1" in plat or "psx" in plat:
            return "PlayStation (PS1)"
        elif "gamecube" in plat or "wii" in plat:
            return "Nintendo GameCube & Wii"
        elif "ds" in plat or "3ds" in plat:
            return "Nintendo DS & 3DS"
        elif "snes" in plat or "super nintendo" in plat:
            return "Super Nintendo (SNES)"
        elif "game boy" in plat or "gba" in plat or "gb" in plat:
            return "Game Boy / Advance"
        elif "sega" in plat or "genesis" in plat or "mega drive" in plat:
            return "Sega Genesis / Retro"
        elif any(k in plat for k in ["dos", "pc", "classic"]):
            return "PC & DOS Classics"
        return "Weitere Systeme"


@dataclass
class InstalledGame:
    id: str
    name: str
    version: str
    install_path: str
    executable_path: str
    installed_at: str
    last_played: str = ""
    playtime_seconds: int = 0
    custom_args: str = ""
    has_assets: bool = False
    latest_available_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstalledGame":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ReleaseInfo:
    tag_name: str
    name: str
    published_at: str
    body: str
    html_url: str
    download_url: str
    asset_name: str
    asset_size: int
