#!/bin/bash
set -e

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
echo "   Deinstallation: Recomp Center                       "
echo "======================================================="

rm -f "$BIN_DIR/recomp-center"
rm -f "$APP_DIR/recomp-center.desktop"
rm -f "$DESKTOP_DIR/recomp-center.desktop" 2>/dev/null || true
rm -f "$HICOLOR_DIR/128x128/apps/recomp-center.png"
rm -f "$PIXMAPS_DIR/recomp-center.png"
rm -rf "$SHARE_DIR/app"

echo "Hinweis: Installierte Spiele unter $SHARE_DIR/games wurden beibehalten."
echo "Wenn du auch alle Spiele löschen möchtest, führe aus: rm -rf $SHARE_DIR"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "[✓] Recomp Center erfolgreich entfernt."
