# Recomp Center – Changelog

Alle wichtigen Änderungen und Neuerungen am Recomp Center werden in dieser Datei dokumentiert.

## [1.0.0] - 2026-09-16

### 🚀 Umfassender Recomp- & Decomp-Katalog (200 Projekte)
- **200 sorgfältig kuratierte Spieleprojekte** über 10 Konsolen- und Computersysteme:
  - **PC & DOS Classics (49 Titel):** Diablo 1 (*DevilutionX*), Fallout 1 & 2 CE, Tomb Raider (*TR1X/TR2X*), Daggerfall Unity, OpenRA, Duke Nukem 3D, Blood, Shadow Warrior u.v.m.
  - **Nintendo 64 (41 Titel):** *Zelda 64: Recompiled* (Majora's Mask & Ocarina of Time), *Banjo-Kazooie: Recompiled*, *DK64*, *Ship of Harkinian*, Mario Kart 64, GoldenEye 007, Mario Party 1–3, Castlevania 64, Pilotwings 64, Pokémon Stadium 2 u.v.m.
  - **Game Boy / Advance (27 Titel):** GBA Recomp, Pokémon Emerald, FireRed, LeafGreen, Crystal, Golden Sun 1 & 2, Zelda: The Minish Cap, Mother 3, Metroid Fusion.
  - **PlayStation / PS1 (24 Titel):** *REDRIVER2* (Driver 2 PC Port), WipEout Rewritten, PSX Doom, Silent Hill, Spyro, Metal Gear Solid, Final Fantasy VII & VIII, Resident Evil 1–3.
  - **Nintendo GameCube & Wii (16 Titel):** Super Mario Sunshine, Wind Waker, Twilight Princess, Melee, Luigi's Mansion, Pikmin 1 & 2, Metroid Prime.
  - **Xbox & Xbox 360 (15 Titel):** Sonic Unleashed Recompiled, Skate 2, Crackdown 1 & 2, Halo 3 Delta, Blue Dragon, Banjo-Kazooie: Nuts & Bolts, XboxRecomp.
  - **Super Nintendo / SNES (12 Titel):** Zelda: A Link to the Past PC Port (`zelda3`), Super Mario World (`smw`), Super Metroid (`sm`), Super Mario RPG, Chrono Trigger.
  - **Nintendo DS & 3DS (9 Titel):** Zelda: OoT 3D, Phantom Hourglass, Spirit Tracks, Super Mario 64 DS, Mario Kart DS, Pokémon HG/SS.
  - **PlayStation 2 (5 Titel):** *OpenGOAL* (Jak and Daxter & Jak II), PS2Recomp, GTA III (`re3`), GTA Vice City (`reVC`).
  - **Sega Genesis / Retro (2 Titel):** Genesis Recomp, Sonic 1 & 2 Decomp.

### ⚡ C-Speed Doctor V64 Byteswap Konvertierung (4 Millisekunden)
- **Extrem schneller Endianness-Konverter:**
  - Konvertiert Doctor V64 Byte-Swapped ROMs (`.v64`, Magic `37 80 40 12`) oder Little-Endian ROMs (`.n64`, Magic `40 12 37 80`) in das von nativen PC-Recomps benötigte Big-Endian Format (`.z64`, Magic `80 37 12 40`).
  - Nutzt Python `array.array('H').byteswap()`, das in compilierter C-Geschwindigkeit arbeitet (ca. 4 Millisekunden für ein vollständiges 16-MB-ROM).
  - Keine externen Tools wie `ucon64` nötig.

### 🎯 1-Klick ROM-Auto-Scanner & Vorbereiter
- **Automatischer Abgleich der eigenen ROM-Sammlung:**
  - Durchsucht mit einem Klick das konfigurierte oder automatisch erkannte ROM-Verzeichnis (z. B. No-Intro-Sammlungen).
  - Erkennt archivierte Spiele (`.zip`) und entpackt diese automatisch.
  - Legt die Spieldatei exakt mit dem vom Port erwarteten Dateinamen (z. B. `baserom.us.z64`, `baserom.mm.us.rev0.z64`) im Spielverzeichnis ab.

### 🎮 Lokale Steam & GOG Auto-Erkennung (1-Klick Import)
- **Nahtlose Desktop-Integration:**
  - Erkennt automatisch Spieldateien in lokalen Steam-Bibliotheken (`~/.local/share/Steam`, `~/.steam`) und GOG-Installationen (`~/Games`).
  - Ermöglicht den 1-Klick-Import der Original-Assets (z. B. `Data.rsdk` für Sonic Mania, `CRITTER.DAT`/`MASTER.DAT` für Fallout 1 & 2, Spieldaten für Dark Forces und Tomb Raider).

### 🎁 Freeware & Demo 1-Klick Download
- **Direkt spielbare Klassiker:**
  - 1-Klick Download der Blizzard Shareware Spieldateien (`spawn.mpq`) für *DevilutionX* (Diablo 1 sofort kostenlos spielbar).
  - 1-Klick Download der offiziellen Bethesda Freeware-Spieldateien für *Daggerfall Unity*.
  - 1-Klick Download spielbarer Demo-Assets für *fheroes2*.

### 🔄 Integrierter GitHub In-App Updater (Cachy Security Suite Architektur)
- **Multi-Komponenten-Update-Center:**
  - Geräuschlose Hintergrundprüfung auf neue Releases via GitHub Releases API beim Start der Anwendung.
  - Dynamischer Indikator in der Sidebar (`● Update verfügbar`), sobald ein neues Release vorliegt.
  - 3-Reiter Dialog:
    - **Status & Komponenten:** Versionen, GitHub-Verknüpfung (Repo & Token), Compiler- & Toolchain-Prüfung (GCC, Clang, CMake, Ninja, Git), Katalog-Status (200 Spiele).
    - **Was ist neu? (Changelog):** Live-Darstellung der neuesten GitHub-Release-Notes sowie des lokalen Changelogs.
    - **Terminal-Ausgabe:** Live-Streaming der Befehlsausgabe mit Protokollierung.
  - 1-Klick Self-Update für Entwickler (`git pull` & Reinstallation) sowie Standalone-Computer (automatischer Tarball-Download & Reinstallation).
  - Sauberer Neustart-Prompt nach erfolgreicher Aktualisierung.
