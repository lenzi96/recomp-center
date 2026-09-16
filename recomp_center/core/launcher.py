"""Game process launcher and directory manager."""

import os
import time
import subprocess
import logging
from datetime import datetime
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QProcess
from .models import InstalledGame
from .library import LibraryManager

logger = logging.getLogger(__name__)


class GameLauncher(QObject):
    game_started = pyqtSignal(str)   # game_id
    game_stopped = pyqtSignal(str)   # game_id
    game_error = pyqtSignal(str, str) # game_id, message

    def __init__(self, library_manager: LibraryManager):
        super().__init__()
        self.library_manager = library_manager
        self.active_processes = {}

    def launch(self, installed_game: InstalledGame) -> Tuple[bool, str]:
        """Launch the game executable."""
        exe_path = installed_game.executable_path

        if not os.path.exists(exe_path):
            msg = f"Ausführbare Datei existiert nicht: {exe_path}"
            self.game_error.emit(installed_game.id, msg)
            return False, msg

        # Ensure executable permission
        if not os.access(exe_path, os.X_OK):
            try:
                os.chmod(exe_path, os.stat(exe_path).st_mode | 0o755)
            except Exception as e:
                msg = f"Konnte Ausführungsrechte nicht setzen: {e}"
                self.game_error.emit(installed_game.id, msg)
                return False, msg

        try:
            cmd = [exe_path]
            if installed_game.custom_args:
                cmd.extend(installed_game.custom_args.split())

            env = os.environ.copy()
            # Set library path if bundled libs exist
            lib_dir = os.path.join(installed_game.install_path, "lib")
            if os.path.exists(lib_dir):
                env["LD_LIBRARY_PATH"] = f"{lib_dir}:{env.get('LD_LIBRARY_PATH', '')}"

            proc = subprocess.Popen(
                cmd,
                cwd=installed_game.install_path,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Update last played
            installed_game.last_played = datetime.now().strftime("%d.%m.%Y %H:%M")
            self.library_manager.save_installed()

            self.active_processes[installed_game.id] = (proc, time.time())
            self.game_started.emit(installed_game.id)
            return True, "Spiel gestartet"

        except Exception as e:
            logger.exception(f"Failed to launch game {installed_game.id}")
            err = f"Fehler beim Starten: {str(e)}"
            self.game_error.emit(installed_game.id, err)
            return False, err

    @staticmethod
    def open_game_folder(folder_path: str):
        """Open game directory in Linux file manager (Nautilus, Dolphin, Thunar, etc.)."""
        if os.path.exists(folder_path):
            try:
                subprocess.Popen(["xdg-open", folder_path])
            except Exception as e:
                logger.error(f"Failed to open directory {folder_path}: {e}")
