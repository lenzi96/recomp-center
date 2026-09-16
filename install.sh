#!/bin/bash
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

mkdir -p "$BIN_DIR" "$APP_DIR" "$SHARE_DIR" "$PIXMAPS_DIR" "$HICOLOR_DIR/128x128/apps"

# 1. Anwendungsdateien nach ~/.local/share/recomp-center/app kopieren
echo "→ Kopiere Anwendungsdateien nach $SHARE_DIR/app..."
mkdir -p "$SHARE_DIR/app"
rm -rf "$SHARE_DIR/app/recomp_center"
cp -r "$DIR/recomp_center" "$SHARE_DIR/app/"
cp "$DIR/main.py" "$SHARE_DIR/app/"
[ -f "$DIR/README.md" ] && cp "$DIR/README.md" "$SHARE_DIR/app/"
echo "[✓] Anwendungsdateien installiert"

# 2. Standalone-Launcher nach ~/.local/bin/recomp-center installieren
echo "→ Installiere Launcher nach $BIN_DIR/recomp-center..."
cat << 'LAUNCHER_EOF' > "$BIN_DIR/recomp-center"
#!/usr/bin/env bash
export PYTHONPATH="$HOME/.local/share/recomp-center/app:${PYTHONPATH}"
exec python3 "$HOME/.local/share/recomp-center/app/main.py" "$@"
LAUNCHER_EOF
chmod 755 "$BIN_DIR/recomp-center"
echo "[✓] Standalone-Launcher installiert"

# 3. Icon installieren
echo "→ Installiere Icons..."
if [ -f "$DIR/recomp-center.png" ]; then
    cp "$DIR/recomp-center.png" "$HICOLOR_DIR/128x128/apps/recomp-center.png"
    cp "$DIR/recomp-center.png" "$PIXMAPS_DIR/recomp-center.png"
fi
echo "[✓] Icons erfolgreich installiert"

# 4. Desktop-Eintrag installieren
echo "→ Installiere Menü-Eintrag..."
cp "$DIR/recomp-center.desktop" "$APP_DIR/recomp-center.desktop"
chmod 644 "$APP_DIR/recomp-center.desktop"

# 5. Optional: Verknüpfung auf Desktop/Schreibtisch
if [ -d "$DESKTOP_DIR" ]; then
    cp "$DIR/recomp-center.desktop" "$DESKTOP_DIR/recomp-center.desktop"
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
