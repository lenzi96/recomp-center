"""Library manager for Recomp Center."""

import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .models import InstalledGame, GameProject

logger = logging.getLogger(__name__)

DEFAULT_BASE_DIR = os.path.expanduser("~/.local/share/recomp-center")
DEFAULT_GAMES_DIR = os.path.join(DEFAULT_BASE_DIR, "games")
CONFIG_FILE = os.path.join(DEFAULT_BASE_DIR, "settings.json")
INSTALLED_DB = os.path.join(DEFAULT_BASE_DIR, "installed.json")
APPLICATIONS_DIR = os.path.expanduser("~/.local/share/applications")


class LibraryManager:
    def __init__(self):
        os.makedirs(DEFAULT_BASE_DIR, exist_ok=True)
        os.makedirs(DEFAULT_GAMES_DIR, exist_ok=True)
        self.settings = self._load_settings()
        self.installed_games: Dict[str, InstalledGame] = self._load_installed()

    def _load_settings(self) -> dict:
        default = {
            "games_dir": DEFAULT_GAMES_DIR,
            "roms_dir": self._auto_detect_default_roms_dir(),
            "github_token": "",
            "auto_check_updates": True,
            "create_desktop_shortcuts": True,
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default.update(data)
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
        return default

    def _auto_detect_default_roms_dir(self) -> str:
        """Autodetects likely ROM locations on user system."""
        import glob
        candidates = [
            "/run/media/julian/HDD/Downloads/N64/Games",
            "/run/media/julian/HDD/Downloads/N64",
            os.path.expanduser("~/ROMs"),
            os.path.expanduser("~/roms"),
            os.path.expanduser("~/Emulation/roms"),
            os.path.expanduser("~/Games/ROMs"),
            os.path.expanduser("~/Downloads"),
        ]
        # Also check /run/media mounts dynamically
        for base in glob.glob("/run/media/*/*"):
            for sub in ["Downloads/N64/Games", "Downloads/N64", "ROMs", "roms", "Emulation/roms"]:
                candidates.append(os.path.join(base, sub))

        for c in candidates:
            if os.path.exists(c):
                return c
        return os.path.expanduser("~/ROMs")

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_games_directory(self) -> str:
        d = self.settings.get("games_dir", DEFAULT_GAMES_DIR)
        os.makedirs(d, exist_ok=True)
        return d

    def set_games_directory(self, path: str):
        self.settings["games_dir"] = path
        self.save_settings()

    def get_roms_directory(self) -> str:
        return self.settings.get("roms_dir", self._auto_detect_default_roms_dir())

    def set_roms_directory(self, path: str):
        self.settings["roms_dir"] = path
        self.save_settings()

    def get_github_token(self) -> str:
        return self.settings.get("github_token", "")

    def set_github_token(self, token: str):
        self.settings["github_token"] = token
        self.save_settings()

    def _load_installed(self) -> Dict[str, InstalledGame]:
        if not os.path.exists(INSTALLED_DB):
            return {}
        try:
            with open(INSTALLED_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: InstalledGame.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load installed games db: {e}")
            return {}

    def save_installed(self):
        try:
            with open(INSTALLED_DB, "w", encoding="utf-8") as f:
                data = {k: v.to_dict() for k, v in self.installed_games.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save installed games db: {e}")

    def register_installed(self, game_id: str, name: str, version: str, install_path: str, exe_path: str) -> InstalledGame:
        installed = InstalledGame(
            id=game_id,
            name=name,
            version=version,
            install_path=install_path,
            executable_path=exe_path,
            installed_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            last_played="Noch nie",
            playtime_seconds=0
        )
        self.installed_games[game_id] = installed
        self.save_installed()
        return installed

    def is_installed(self, game_id: str) -> bool:
        return game_id in self.installed_games and os.path.exists(self.installed_games[game_id].install_path)

    def get_installed(self, game_id: str) -> Optional[InstalledGame]:
        return self.installed_games.get(game_id)

    def uninstall(self, game_id: str) -> bool:
        if game_id not in self.installed_games:
            return False

        game = self.installed_games[game_id]
        # Remove game folder
        if os.path.exists(game.install_path):
            try:
                shutil.rmtree(game.install_path)
            except Exception as e:
                logger.error(f"Failed to remove game folder {game.install_path}: {e}")

        # Remove desktop file if exists
        self.remove_desktop_entry(game_id)

        del self.installed_games[game_id]
        self.save_installed()
        return True

    def check_game_assets(self, project: GameProject) -> Tuple[bool, List[str]]:
        """
        Check if required assets/ROMs exist in the installed game directory.
        Returns (all_present: bool, missing_files: list)
        """
        if not self.is_installed(project.id):
            return False, project.required_files

        if not project.required_files:
            return True, []

        game = self.installed_games[project.id]
        missing = []

        for req in project.required_files:
            req_lower = req.lower()
            found = False
            for root, _, files in os.walk(game.install_path):
                for f in files:
                    if f.lower() == req_lower:
                        found = True
                        break
                if found:
                    break
            if not found:
                missing.append(req)

        return (len(missing) == 0), missing

    def create_desktop_entry(self, project: GameProject) -> bool:
        """Create an XDG .desktop entry for easy launching from application menu."""
        if not self.is_installed(project.id):
            return False

        game = self.installed_games[project.id]
        desktop_filename = f"recomp-{project.id}.desktop"
        desktop_path = os.path.join(APPLICATIONS_DIR, desktop_filename)

        os.makedirs(APPLICATIONS_DIR, exist_ok=True)

        content = f"""[Desktop Entry]
Name={project.name}
Comment={project.short_desc}
Exec="{game.executable_path}" {game.custom_args}
Path={game.install_path}
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Emulator;
StartupNotify=true
"""
        try:
            with open(desktop_path, "w", encoding="utf-8") as f:
                f.write(content)
            os.chmod(desktop_path, 0o755)
            return True
        except Exception as e:
            logger.error(f"Failed to write desktop entry: {e}")
            return False

    def remove_desktop_entry(self, game_id: str):
        desktop_filename = f"recomp-{game_id}.desktop"
        desktop_path = os.path.join(APPLICATIONS_DIR, desktop_filename)
        if os.path.exists(desktop_path):
            try:
                os.remove(desktop_path)
            except Exception:
                pass
