#!/bin/bash
# ==============================================================================
# Recomp Center - Terminal Installer
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
SHARE_DIR="$HOME/.local/share/recomp-center"
HICOLOR_DIR="$HOME/.local/share/icons/hicolor"
PIXMAPS_DIR="$HOME/.local/share/pixmaps"

DESKTOP_DIR="$HOME/Desktop"
if [ -d "$HOME/Schreibtisch" ]; then
    DESKTOP_DIR="$HOME/Schreibtisch"
fi

echo "======================================================="
echo "   Installation: Recomp Center                         "
echo "======================================================="

# 0. Dependency Check
echo "→ Prüfe System-Abhängigkeiten..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[FEHLER] Python 3 ist nicht installiert!" >&2
    exit 1
fi

if ! python3 -c "import PyQt6" >/dev/null 2>&1; then
    echo "[!] PyQt6 ist noch nicht installiert. Versuche Installation..."
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed python-pyqt6 || true
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3-pyqt6 || true
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-pyqt6 || true
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper in -y python3-qt6 || true
    fi
fi

mkdir -p "$BIN_DIR" "$APP_DIR" "$SHARE_DIR" "$PIXMAPS_DIR" "$HICOLOR_DIR/128x128/apps"

# 1. Anwendungsdateien nach ~/.local/share/recomp-center/app kopieren
echo "→ Kopiere Anwendungsdateien nach $SHARE_DIR/app..."
mkdir -p "$SHARE_DIR/app"
rm -rf "$SHARE_DIR/app/recomp_center"
cp -r "$DIR/recomp_center" "$SHARE_DIR/app/"
cp "$DIR/main.py" "$SHARE_DIR/app/"
cp "$DIR/recomp-center" "$SHARE_DIR/app/"
[ -f "$DIR/README.md" ] && cp "$DIR/README.md" "$SHARE_DIR/app/"
[ -f "$DIR/CHANGELOG.md" ] && cp "$DIR/CHANGELOG.md" "$SHARE_DIR/app/"

# Git-Ordner kopieren falls vorhanden (für In-App Updater)
if [ -d "$DIR/.git" ]; then
    rm -rf "$SHARE_DIR/app/.git"
    cp -r "$DIR/.git" "$SHARE_DIR/app/"
fi
echo "[✓] Anwendungsdateien installiert"

# 2. Standalone-Launcher nach ~/.local/bin/recomp-center installieren
echo "→ Installiere Launcher nach $BIN_DIR/recomp-center..."
cp "$DIR/recomp-center" "$BIN_DIR/recomp-center"
chmod 755 "$BIN_DIR/recomp-center"
chmod 755 "$SHARE_DIR/app/main.py"
chmod 755 "$SHARE_DIR/app/recomp-center"
echo "[✓] Standalone-Launcher installiert"

# 3. Icon installieren
echo "→ Installiere Icons..."
if [ -f "$DIR/recomp-center.png" ]; then
    cp "$DIR/recomp-center.png" "$HICOLOR_DIR/128x128/apps/recomp-center.png"
    cp "$DIR/recomp-center.png" "$PIXMAPS_DIR/recomp-center.png"
fi
echo "[✓] Icons erfolgreich installiert"

# 4. Desktop-Eintrag installieren (mit robustem Exec-Pfad)
echo "→ Installiere Menü-Eintrag..."
TARGET_DESKTOP="$APP_DIR/recomp-center.desktop"
sed "s|^Exec=.*|Exec=sh -c 'if [ -x \"$BIN_DIR/recomp-center\" ]; then exec \"$BIN_DIR/recomp-center\" \"\$@\"; else exec recomp-center \"\$@\"; fi' -- %u|" "$DIR/recomp-center.desktop" > "$TARGET_DESKTOP"
chmod 644 "$TARGET_DESKTOP"

# 5. Optional: Verknüpfung auf Desktop/Schreibtisch
if [ -d "$DESKTOP_DIR" ]; then
    cp "$TARGET_DESKTOP" "$DESKTOP_DIR/recomp-center.desktop"
    chmod +x "$DESKTOP_DIR/recomp-center.desktop" 2>/dev/null || true
    echo "[✓] Desktop-Verknüpfung erstellt auf $DESKTOP_DIR"
fi

# Update Icon Cache & Desktop Database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HICOLOR_DIR" 2>/dev/null || true
fi

echo "======================================================="
echo "   [✓] Recomp Center erfolgreich installiert!          "
echo "   Startbar über: recomp-center oder im Anwendungsmenü "
echo "======================================================="
