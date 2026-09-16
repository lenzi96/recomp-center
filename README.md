# ⚡ Recomp Center

Ein modernes, natives Linux-GUI-Zentrum (PyQt6) zum **Entdecken, Herunterladen, Aktualisieren und Verwalten aller bekannten Recomp- und Decomp-Projekte**.

Bietet eine All-in-One-Oberfläche für statische Rekompilationen (*Zelda 64: Recompiled*), native Decompilierungs-Ports (*Ship of Harkinian*, *OpenGOAL*, *DevilutionX*, *Sonic Mania*, *TR1X*, *Fallout CE*) sowie eine durchsuchbare Datenbank von über 80+ Source-Decomp-Projekten.

---

## 🚀 Features

- **🎮 Umfangreicher Spiele-Katalog:**
  - **N64 Recompiled:** Zelda 64: Recompiled (Majora's Mask & OoT), Perfect Dark Recompiled, Dinosaur Planet Recomp.
  - **Playable Decomp Ports:** Ship of Harkinian, 2 Ship 2 Harkinian, OpenGOAL (Jak 1 & 2), DevilutionX (Diablo 1), Fallout 1 CE, Fallout 2 CE, The Force Engine (Dark Forces), TR1X & TR2X, Sonic Mania / CD / 1-2 Decomps, fheroes2, Daggerfall Unity, OpenRCT2, Augustus u.v.m.
  - **Source Decompilations:** Direkter Zugriff auf Repositories (Mario 64, Banjo-Kazooie, Conker, Paper Mario, Pokémon Emerald, Castlevania SOTN, GTA III re3 u.v.m.).
- **⬇ 1-Klick Downloader & Installer:**
  - Findet automatisch die passenden Linux-Binaries (AppImage, `x86_64.tar.gz`, `zip`) aus den offiziellen GitHub-Releases.
  - Asynchroner Download mit Fortschrittsanzeige, Entpackung und Rechteregistrierung (`chmod +x`).
- **💾 ROM- & Asset-Assistent:**
  - Übersichtliche Anzeige, welche Spieldateien / ROMs für das jeweilige Spiel erforderlich sind (z. B. `baserom.mm.us.rev0.z64`, `DIABDAT.MPQ`, `CRITTER.DAT`).
  - Integrierter Import-Button oder 1-Klick-Öffnen des Ordners im System-Dateimanager.
- **▶ Game Launcher & Desktop-Integration:**
  - Spiele direkt aus dem Recomp Center starten.
  - Optionale Erstellung von `.desktop`-Dateien für das Linux-Anwendungsmenü.
- **🎨 Modernes Dark-Slate UI:**
  - Einheitliches Design im Stil von *Gaming Center* und *Linux Cleaner GUI*.
  - Einzelinstanz-Schutz (Single-Instance IPC).

---

## 🛠️ Installation & Start

### Schnellstart (ohne Installation)
```bash
cd recomp-center
./recomp-center
# oder:
python3 main.py
```

### 🖥️ Grafischer Installations-Assistent (Empfohlen)
```bash
./install-gui.sh
# oder:
python3 installer_gui.py
```
Öffnet einen interaktiven 4-Schritte Setup-Assistenten mit System-Voraussetzungsprüfung, automatischer ROM-Verzeichnis-Erkennung und Desktop-Integration.

### ⚡ Schnelle Terminal-Installation
```bash
./install.sh
```
Installiert Recomp Center nach `~/.local/share/recomp-center/app`, verlinkt den Starter nach `~/.local/bin/recomp-center` und richtet das Anwendungsmenü sowie Schreibtisch-Icon ein.

### Deinstallation
```bash
./uninstall.sh
```

---

## ⚖️ Rechtlicher Hinweis

*Recomp Center* lädt ausschließlich die quelloffenen Engine-Binaries und Ports von den offiziellen Open-Source-Repositories der Entwickler herunter. 
Urheberrechtlich geschützte Spieldaten, Texturen, Audio-Dateien und ROMs sind **nicht** enthalten und müssen vom Nutzer aus rechtmäßig erworbenen Originalkopien bereitgestellt werden.
