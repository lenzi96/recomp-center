"""
Build and compilation engine for Source Ports and Decompilation projects.
Handles git cloning, dependency checking, compiling via make/cmake, and registration.
"""

import os
import stat
import shutil
import subprocess
import multiprocessing
from typing import List, Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal

from .models import GameProject
from .library import LibraryManager
from .extractor import Extractor


class BuildWorker(QThread):
    step_changed = pyqtSignal(str)       # Step name
    log_output = pyqtSignal(str)         # Line of output
    build_finished = pyqtSignal(bool, str, str)  # success, exe_path, message

    def __init__(self, project: GameProject, library_mgr: LibraryManager):
        super().__init__()
        self.project = project
        self.library_mgr = library_mgr
        self._is_cancelled = False
        self._current_proc: Optional[subprocess.Popen] = None

        base_dir = os.path.expanduser("~/.local/share/recomp-center")
        self.sources_dir = os.path.join(base_dir, "sources", self.project.id)
        self.target_game_dir = os.path.join(self.library_mgr.get_games_directory(), self.project.id)

    def cancel(self):
        self._is_cancelled = True
        if self._current_proc and self._current_proc.poll() is None:
            try:
                self._current_proc.terminate()
            except Exception:
                pass

    def run(self):
        try:
            os.makedirs(self.sources_dir, exist_ok=True)
            cores = multiprocessing.cpu_count()

            # ---------------------------------------------------------
            # Step 1: Clone or Update Git Repository
            # ---------------------------------------------------------
            self.step_changed.emit("1/4: Quellcode abrufen (Git)...")
            self.log_output.emit(f"=== [Schritt 1] Repository: {self.project.github_url} ===")

            if not os.path.exists(os.path.join(self.sources_dir, ".git")):
                self.log_output.emit(f"Klone Quellcode nach {self.sources_dir}...")
                clone_cmd = ["git", "clone", "--recursive", self.project.github_url, self.sources_dir]
                if not self._run_command(clone_cmd, cwd=os.path.dirname(self.sources_dir)):
                    self.build_finished.emit(False, "", "Git Clone fehlgeschlagen.")
                    return
            else:
                self.log_output.emit("Bestehendes Quellcode-Repository gefunden. Aktualisiere...")
                pull_cmd = ["git", "pull", "--recurse-submodules"]
                self._run_command(pull_cmd, cwd=self.sources_dir)

            if self._is_cancelled:
                self.build_finished.emit(False, "", "Vorgang abgebrochen.")
                return

            # ---------------------------------------------------------
            # Step 2: Check Required Asset / ROM Dependencies
            # ---------------------------------------------------------
            self.step_changed.emit("2/4: Spieldateien & ROMs prüfen...")
            self.log_output.emit("=== [Schritt 2] Assets prüfen ===")

            if self.project.required_files:
                missing = []
                for req in self.project.required_files:
                    # Check in sources_dir or in installed game dir
                    found = False
                    for root, _, files in os.walk(self.sources_dir):
                        if any(f.lower() == req.lower() for f in files):
                            found = True
                            break
                    if not found:
                        missing.append(req)

                if missing:
                    msg = (
                        f"Fehlende Spieldatei(en) im Quellverzeichnis:\n"
                        f"{', '.join(missing)}\n\n"
                        f"Bitte lege die Datei(en) in folgenden Ordner ab:\n{self.sources_dir}"
                    )
                    self.log_output.emit(f"FEHLER: {msg}")
                    self.build_finished.emit(False, "", msg)
                    return
                else:
                    self.log_output.emit("Alle erforderlichen Spieldateien vorhanden.")

            # ---------------------------------------------------------
            # Step 3: Compiling Source Code
            # ---------------------------------------------------------
            self.step_changed.emit("3/4: Kompilieren...")
            self.log_output.emit(f"=== [Schritt 3] Kompilierung starten (Threads: {cores}) ===")

            build_success = False

            if self.project.build_commands:
                # Custom defined commands
                for cmd_str in self.project.build_commands:
                    cmd_formatted = cmd_str.replace("{nproc}", str(cores))
                    self.log_output.emit(f"Führe aus: {cmd_formatted}")
                    if not self._run_command(cmd_formatted, shell=True, cwd=self.sources_dir):
                        self.build_finished.emit(False, "", f"Befehl fehlgeschlagen: {cmd_formatted}")
                        return
                build_success = True

            elif os.path.exists(os.path.join(self.sources_dir, "CMakeLists.txt")):
                self.log_output.emit("CMake-Projekt erkannt.")
                if not shutil.which("cmake"):
                    msg = "CMake ist nicht installiert. Bitte installiere es über 'sudo pacman -S cmake'."
                    self.log_output.emit(f"FEHLER: {msg}")
                    self.build_finished.emit(False, "", msg)
                    return

                cmake_config = ["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"]
                if not self._run_command(cmake_config, cwd=self.sources_dir):
                    self.build_finished.emit(False, "", "CMake Konfiguration fehlgeschlagen.")
                    return

                cmake_build = ["cmake", "--build", "build", "-j", str(cores)]
                if not self._run_command(cmake_build, cwd=self.sources_dir):
                    self.build_finished.emit(False, "", "CMake Build fehlgeschlagen.")
                    return
                build_success = True

            elif os.path.exists(os.path.join(self.sources_dir, "Makefile")):
                self.log_output.emit("Makefile erkannt. Verwende GNU Make...")
                make_cmd = ["make", f"-j{cores}"]
                if not self._run_command(make_cmd, cwd=self.sources_dir):
                    self.build_finished.emit(False, "", "Make-Befehl fehlgeschlagen.")
                    return
                build_success = True

            elif os.path.exists(os.path.join(self.sources_dir, "Cargo.toml")):
                self.log_output.emit("Rust/Cargo Projekt erkannt...")
                cargo_cmd = ["cargo", "build", "--release"]
                if not self._run_command(cargo_cmd, cwd=self.sources_dir):
                    self.build_finished.emit(False, "", "Cargo Build fehlgeschlagen.")
                    return
                build_success = True

            else:
                msg = "Kein bekanntes Build-System (Makefile, CMakeLists.txt oder Cargo.toml) im Quellverzeichnis gefunden."
                self.log_output.emit(f"FEHLER: {msg}")
                self.build_finished.emit(False, "", msg)
                return

            if self._is_cancelled:
                self.build_finished.emit(False, "", "Kompilierung abgebrochen.")
                return

            # ---------------------------------------------------------
            # Step 4: Locate Executable & Register in Library
            # ---------------------------------------------------------
            self.step_changed.emit("4/4: Binärdatei registrieren...")
            self.log_output.emit("=== [Schritt 4] Executable suchen & registrieren ===")

            exe_path = Extractor._find_executable(self.sources_dir, self.project.executable_hints)

            if not exe_path:
                msg = "Kompilierung beendet, aber keine ausführbare Binärdatei gefunden."
                self.log_output.emit(f"WARNUNG: {msg}")
                self.build_finished.emit(False, "", msg)
                return

            # Ensure executable permission
            current_mode = os.stat(exe_path).st_mode
            os.chmod(exe_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            # Copy or link to games directory
            os.makedirs(self.target_game_dir, exist_ok=True)
            target_exe = os.path.join(self.target_game_dir, os.path.basename(exe_path))

            try:
                # Copy executable and any adjacent shared libraries/data
                shutil.copy2(exe_path, target_exe)
                os.chmod(target_exe, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                final_exe = target_exe
                final_dir = self.target_game_dir
            except Exception as e:
                self.log_output.emit(f"Hinweis: Verwende Binary direkt im Quellordner ({e})")
                final_exe = exe_path
                final_dir = os.path.dirname(exe_path)

            self.library_mgr.register_installed(
                game_id=self.project.id,
                name=self.project.name,
                version="Custom Source Build",
                install_path=final_dir,
                exe_path=final_exe
            )

            if self.library_mgr.settings.get("create_desktop_shortcuts", True):
                self.library_mgr.create_desktop_entry(self.project)

            self.log_output.emit(f"ERFOLG: Spiel registriert unter: {final_exe}")
            self.build_finished.emit(True, final_exe, "Erfolgreich kompiliert und installiert!")

        except Exception as e:
            self.log_output.emit(f"KRITISCHER FEHLER: {str(e)}")
            self.build_finished.emit(False, "", str(e))

    def _run_command(self, cmd, cwd: str, shell: bool = False) -> bool:
        """Runs a subprocess command and streams stdout and stderr in real-time."""
        try:
            self._current_proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in iter(self._current_proc.stdout.readline, ''):
                if self._is_cancelled:
                    self._current_proc.terminate()
                    return False
                line_clean = line.rstrip()
                if line_clean:
                    self.log_output.emit(line_clean)

            self._current_proc.stdout.close()
            return_code = self._current_proc.wait()
            return return_code == 0

        except Exception as e:
            self.log_output.emit(f"Fehler bei Befehlsausführung: {e}")
            return False
