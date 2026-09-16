#!/usr/bin/env python3
"""Entry point for Recomp Center."""

import sys
import shutil
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def check_runtime_dependencies() -> bool:
    """Verifies that all required GUI runtime libraries are installed."""
    missing = []
    try:
        import PyQt6
        from PyQt6 import QtCore, QtGui, QtWidgets
    except ImportError:
        missing.append("PyQt6 (python-pyqt6)")

    if not missing:
        return True

    msg = (
        "Recomp Center benötigt PyQt6, das auf diesem System noch nicht installiert ist.\n\n"
        "Bitte installiere das Paket mit deinem Paketmanager:\n\n"
        "  • Arch Linux / CachyOS:   sudo pacman -S python-pyqt6\n"
        "  • Ubuntu / Debian / Mint:  sudo apt install python3-pyqt6\n"
        "  • Fedora / RHEL:           sudo dnf install python3-pyqt6\n"
        "  • openSUSE:                sudo zypper in python3-qt6\n"
        "  • Python PIP:              pip install PyQt6\n"
    )
    print("\033[1;31m[FEHLER]\033[0m " + msg, file=sys.stderr)

    # Show visual message box if running in a desktop session
    if shutil.which("zenity"):
        subprocess.run(["zenity", "--error", "--title=Recomp Center", "--text=" + msg], check=False)
    elif shutil.which("kdialog"):
        subprocess.run(["kdialog", "--error", msg, "--title", "Recomp Center"], check=False)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", "-u", "critical", "Recomp Center", "PyQt6 fehlt! Bitte 'python-pyqt6' installieren."], check=False)

    return False


if __name__ == "__main__":
    if not check_runtime_dependencies():
        sys.exit(1)
    from recomp_center.app import main
    main()
