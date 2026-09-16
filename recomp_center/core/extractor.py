"""Extractor for downloaded game packages and AppImages."""

import os
import stat
import shutil
import zipfile
import tarfile
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Extractor:
    @staticmethod
    def install_package(archive_path: str, destination_dir: str, executable_hints: List[str]) -> Tuple[bool, str, str]:
        """
        Extracts archive or installs AppImage/binary into destination_dir.
        Returns: (success: bool, executable_path: str, error_message: str)
        """
        try:
            os.makedirs(destination_dir, exist_ok=True)
            filename = os.path.basename(archive_path).lower()

            if filename.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as z:
                    z.extractall(destination_dir)
            elif filename.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".tar")):
                with tarfile.open(archive_path, 'r:*') as t:
                    t.extractall(destination_dir)
            elif filename.endswith(".appimage") or not ("." in filename):
                # Single binary / AppImage
                target_file = os.path.join(destination_dir, os.path.basename(archive_path))
                shutil.copy2(archive_path, target_file)
            else:
                # Unknown format, try copying as file
                target_file = os.path.join(destination_dir, os.path.basename(archive_path))
                shutil.copy2(archive_path, target_file)

            # Locate executable
            exe_path = Extractor._find_executable(destination_dir, executable_hints)
            if exe_path and os.path.exists(exe_path):
                # Ensure chmod +x
                current_mode = os.stat(exe_path).st_mode
                os.chmod(exe_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                return True, exe_path, ""
            elif os.path.exists(destination_dir):
                # Could not detect exact executable, pick first candidate or dir
                candidates = Extractor._list_all_files(destination_dir)
                for c in candidates:
                    if os.access(c, os.X_OK) and not os.path.isdir(c):
                        return True, c, ""
                return True, destination_dir, ""

            return False, "", "Konnte ausführbare Datei nach dem Entpacken nicht finden."

        except Exception as e:
            logger.exception("Extraction failed")
            return False, "", str(e)

    @staticmethod
    def _find_executable(base_dir: str, hints: List[str]) -> Optional[str]:
        """Search recursively for an executable matching hints or AppImage."""
        # 1. Match hints exactly or case-insensitively
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # AppImages are always prioritized
                if file.lower().endswith(".appimage"):
                    return full_path
                for hint in hints:
                    if hint.lower() in file.lower():
                        return full_path

        # 2. Check for ELF binaries
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if Extractor._is_elf_binary(full_path):
                    # Exclude typical shared objects / libraries
                    if not file.endswith((".so", ".so.1", ".dll", ".dylib")):
                        return full_path

        return None

    @staticmethod
    def _is_elf_binary(file_path: str) -> bool:
        """Check if file has ELF header."""
        try:
            if not os.path.isfile(file_path) or os.path.islink(file_path):
                return False
            with open(file_path, "rb") as f:
                header = f.read(4)
                return header == b"\x7fELF"
        except Exception:
            return False

    @staticmethod
    def _list_all_files(base_dir: str) -> List[str]:
        result = []
        for root, _, files in os.walk(base_dir):
            for f in files:
                result.append(os.path.join(root, f))
        return result
