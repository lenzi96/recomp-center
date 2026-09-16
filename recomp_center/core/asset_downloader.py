"""
Asset Downloader and Steam/GOG Auto-Detection for Recomp Center.
Provides 1-click downloads for official free/demo/shareware assets,
automatic local Steam/GOG detection and extraction, and custom URL downloading.
"""

import os
import shutil
import zipfile
import tarfile
import urllib.request
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal

# -----------------------------------------------------------------
# 1. Curated Legal Free / Demo / Shareware Asset Sources
# -----------------------------------------------------------------
FREE_ASSET_PACKS = {
    "devilutionx": {
        "title": "Blizzard Diablo 1 Shareware (spawn.mpq)",
        "url": "https://github.com/diasurgical/devilutionX/releases/download/1.5.3/spawn.mpq",
        "filename": "spawn.mpq",
        "desc": "Offizielle kostenlose Diablo 1 Demo/Shareware-Daten. Spielbar ohne Kauf der Vollversion!"
    },
    "daggerfall-unity": {
        "title": "The Elder Scrolls II: Daggerfall (Bethesda Freeware)",
        "url": "https://github.com/Interkarma/daggerfall-unity/releases/download/v0.16.1-beta/DFU-GameFiles.zip",
        "filename": "DFU-GameFiles.zip",
        "desc": "Vollständige Original-Spieldaten, von Bethesda offiziell als Freeware veröffentlicht."
    },
    "fheroes2": {
        "title": "Heroes of Might and Magic II Demo-Dateien",
        "url": "https://github.com/ihhub/fheroes2/releases/download/1.0.12/fheroes2_demo.zip",
        "filename": "fheroes2_demo.zip",
        "desc": "Offizielle spielbare Demo-Assets für Heroes of Might and Magic II."
    }
}


# -----------------------------------------------------------------
# 2. Local Steam & GOG Asset Auto-Detector
# -----------------------------------------------------------------
class SteamGOGScanner:
    """Scans local Steam and GOG installations for legitimate owned game files."""

    KNOWN_SEARCH_PATHS = [
        os.path.expanduser("~/.local/share/Steam/steamapps/common"),
        os.path.expanduser("~/.steam/steam/steamapps/common"),
        os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common"),
        os.path.expanduser("~/Games"),
        os.path.expanduser("~/GOG Games"),
        os.path.expanduser("~/.wine/drive_c/Program Files (x86)/GOG Galaxy/Games")
    ]

    # Mapping from project_id to relative paths or directories inside Steam/GOG
    GAME_SIGS = {
        "sonic-mania": {
            "dirs": ["Sonic Mania"],
            "files": ["Data.rsdk"]
        },
        "sonic-cd-11": {
            "dirs": ["Sonic CD", "Sonic CD (2011)"],
            "files": ["Data.rsdk"]
        },
        "fallout1-ce": {
            "dirs": ["Fallout", "Fallout 1"],
            "files": ["CRITTER.DAT", "MASTER.DAT"]
        },
        "fallout2-ce": {
            "dirs": ["Fallout 2"],
            "files": ["CRITTER.DAT", "MASTER.DAT"]
        },
        "the-force-engine": {
            "dirs": ["STAR WARS Dark Forces", "Dark Forces"],
            "files": ["DARK.GOB"]
        },
        "tr1x": {
            "dirs": ["Tomb Raider (I)", "Tomb Raider I", "TombRaider1"],
            "files": ["GAME.DAT"]
        },
        "tr2x": {
            "dirs": ["Tomb Raider (II)", "Tomb Raider II", "TombRaider2"],
            "files": ["MAIN.SFX"]
        },
        "openrct2": {
            "dirs": ["RollerCoaster Tycoon 2", "RollerCoaster Tycoon 2 Triple Thrill Pack"],
            "files": ["Data/g1.dat"]
        },
        "corsix-th": {
            "dirs": ["Theme Hospital"],
            "files": ["Hosp/MPL0001.DAT"]
        }
    }

    @classmethod
    def scan_for_game(cls, project_id: str) -> Optional[Dict[str, str]]:
        """
        Scans local drives for the given game.
        Returns dict with 'found_dir' and 'files' if detected.
        """
        if project_id not in cls.GAME_SIGS:
            return None

        sig = cls.GAME_SIGS[project_id]

        for base_path in cls.KNOWN_SEARCH_PATHS:
            if not os.path.exists(base_path):
                continue

            for cand_dir in sig["dirs"]:
                full_dir = os.path.join(base_path, cand_dir)
                if os.path.exists(full_dir):
                    # Verify at least one file exists
                    found_any = False
                    for f in sig["files"]:
                        if os.path.exists(os.path.join(full_dir, f)):
                            found_any = True
                            break
                    if found_any:
                        return {
                            "game_dir": full_dir,
                            "files": sig["files"]
                        }

        return None

    @classmethod
    def copy_from_steam(cls, source_dir: str, target_dir: str, required_files: List[str]) -> Tuple[int, str]:
        """Copies all matching files and folders into target_dir."""
        os.makedirs(target_dir, exist_ok=True)
        copied = 0
        try:
            for root, dirs, files in os.walk(source_dir):
                for f in files:
                    for req in required_files:
                        if f.lower() == os.path.basename(req).lower():
                            src_file = os.path.join(root, f)
                            dst_file = os.path.join(target_dir, f)
                            shutil.copy2(src_file, dst_file)
                            copied += 1

            # Also copy entire data folders if present
            for folder in ["Data", "data", "sound", "Sound"]:
                src_folder = os.path.join(source_dir, folder)
                if os.path.exists(src_folder):
                    dst_folder = os.path.join(target_dir, folder)
                    if not os.path.exists(dst_folder):
                        shutil.copytree(src_folder, dst_folder)
                        copied += 1

            return copied, "Dateien erfolgreich importiert!"
        except Exception as e:
            return copied, f"Fehler beim Kopieren: {e}"


# -----------------------------------------------------------------
# 3. Asynchronous Asset Download Worker
# -----------------------------------------------------------------
class AssetDownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)   # current, total, speed
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url: str, target_dir: str, filename: str):
        super().__init__()
        self.url = url
        self.target_dir = target_dir
        self.filename = filename
        self._is_cancelled = False
        self.target_path = os.path.join(target_dir, filename)

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            self.status.emit(f"Verbindung wird aufgebaut: {self.filename}...")

            req = urllib.request.Request(self.url, headers={"User-Agent": "RecompCenter-AssetDownloader/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                with open(self.target_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if os.path.exists(self.target_path):
                                os.remove(self.target_path)
                            self.finished.emit(False, "Download abgebrochen.")
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int((downloaded / total_size) * 100) if total_size else 0
                        self.progress.emit(downloaded, total_size, f"{percent}%")

            self.status.emit("Download abgeschlossen. Entpacke ggf. Archiv...")

            # If it's a zip or tar archive, extract directly into target_dir
            lower_name = self.filename.lower()
            if lower_name.endswith(".zip"):
                with zipfile.ZipFile(self.target_path, 'r') as z:
                    z.extractall(self.target_dir)
                try:
                    os.remove(self.target_path)
                except Exception:
                    pass
            elif lower_name.endswith((".tar.gz", ".tgz", ".tar.xz")):
                with tarfile.open(self.target_path, 'r:*') as t:
                    t.extractall(self.target_dir)
                try:
                    os.remove(self.target_path)
                except Exception:
                    pass

            self.finished.emit(True, "Spieldateien erfolgreich heruntergeladen und bereitgestellt!")

        except Exception as e:
            if os.path.exists(self.target_path):
                try:
                    os.remove(self.target_path)
                except Exception:
                    pass
            self.finished.emit(False, f"Fehler beim Download: {str(e)}")
