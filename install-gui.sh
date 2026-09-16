#!/bin/bash
# ==============================================================================
# Recomp Center - Graphical Installer Launcher
# Checks dependencies and launches installer_gui.py
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "\033[1;31m[FEHLER] Python 3 ist nicht installiert!\033[0m" >&2
    exit 1
fi

# Check if PyQt6 is available for the graphical wizard
if ! python3 -c "import PyQt6" >/dev/null 2>&1; then
    echo -e "\033[1;33m[!] PyQt6 ist für den grafischen Installations-Assistenten erforderlich.\033[0m"
    echo "Versuche automatische Installation der Abhängigkeit..."
    INSTALLED=false

    if command -v pacman >/dev/null 2>&1; then
        echo "Führe aus: sudo pacman -S --needed python-pyqt6"
        sudo pacman -S --needed python-pyqt6 && INSTALLED=true || true
    elif command -v apt-get >/dev/null 2>&1; then
        echo "Führe aus: sudo apt-get install -y python3-pyqt6"
        sudo apt-get update && sudo apt-get install -y python3-pyqt6 && INSTALLED=true || true
    elif command -v dnf >/dev/null 2>&1; then
        echo "Führe aus: sudo dnf install -y python3-pyqt6"
        sudo dnf install -y python3-pyqt6 && INSTALLED=true || true
    elif command -v zypper >/dev/null 2>&1; then
        echo "Führe aus: sudo zypper in -y python3-qt6"
        sudo zypper in -y python3-qt6 && INSTALLED=true || true
    fi

    if [ "$INSTALLED" = false ] && ! python3 -c "import PyQt6" >/dev/null 2>&1; then
        echo -e "\n\033[1;31m[Hinweis] PyQt6 konnte nicht automatisch installiert werden.\033[0m"
        echo "Starte stattdessen die textbasierte Terminal-Installation:"
        exec "$DIR/install.sh" "$@"
    fi
fi

exec python3 "$DIR/installer_gui.py" "$@"
