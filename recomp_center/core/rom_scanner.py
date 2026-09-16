"""
ROM Scanner and Auto-Matcher for Recomp Center.
Scans configured local ROM directories, identifies matching ROMs by name/patterns,
unzips if needed, automatically converts endianness (.v64/.n64 -> .z64),
and copies them into the game folder with the required baserom filename.
"""

import os
import glob
import array
import zipfile
import shutil
import logging
from typing import List, Optional, Tuple, Dict
from .models import GameProject

logger = logging.getLogger(__name__)

# Magic byte signatures for N64 ROMs
MAGIC_Z64_BIG_ENDIAN = b'\x80\x37\x12\x40'       # Native (.z64)
MAGIC_V64_BYTESWAPPED = b'\x37\x80\x40\x12'      # Doctor V64 (.v64)
MAGIC_N64_LITTLE_ENDIAN = b'\x40\x12\x37\x80'    # CD64 (.n64)

# Heuristic keyword matchers for games to identify ROM files
ROM_MATCH_RULES: Dict[str, Dict[str, any]] = {
    "zelda-64-recomp": {
        "keywords": ["majora's mask", "majora"],
        "excludes": ["randomizer", "oot", "ocarina"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.mm.us.rev0.z64"
    },
    "ship-of-harkinian": {
        "keywords": ["ocarina of time", "ocarina"],
        "excludes": ["majora"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "2-ship-2-harkinian": {
        "keywords": ["majora's mask", "majora"],
        "excludes": ["ocarina"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.mm.us.rev0.z64"
    },
    "sm64ex": {
        "keywords": ["super mario 64", "mario 64"],
        "excludes": ["ds", "land", "kart", "party", "tennis", "golf", "paper"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "sm64-port": {
        "keywords": ["super mario 64", "mario 64"],
        "excludes": ["ds", "land", "kart", "party", "tennis", "golf", "paper"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "perfect-dark-recomp": {
        "keywords": ["perfect dark", "perfect_dark"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "banjo-recomp": {
        "keywords": ["banjo-kazooie", "banjo kazooie", "banjokazooie"],
        "excludes": ["tooie", "nuts"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "snowboard-kids-2-recomp": {
        "keywords": ["snowboard kids 2", "snowboardkids2", "snowboard kids ii"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "quest-64-recomp": {
        "keywords": ["quest 64", "quest64", "holy magic century"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "dk64-recomp": {
        "keywords": ["donkey kong 64", "donkey kong - 64"],
        "excludes": ["country"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "dinosaur-planet-recomp": {
        "keywords": ["dinosaur planet", "dinosaurplanet"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".zip"],
        "target_name": "baserom.z64"
    },
    "glover-recomp": {
        "keywords": ["glover"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "superman-64-recomp": {
        "keywords": ["superman 64", "superman (usa)", "superman (europe)"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "drmario-64-recomp": {
        "keywords": ["dr. mario 64", "dr mario 64", "drmario 64"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "fzerox-decomp": {
        "keywords": ["f-zero x", "fzerox"],
        "excludes": ["gx", "maximum", "climax", "gp"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "diddy-kong-racing": {
        "keywords": ["diddy kong racing"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "mario-kart-64": {
        "keywords": ["mario kart 64", "mariokart 64"],
        "excludes": ["super circuit", "double dash", "wii", "7", "8"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "paper-mario": {
        "keywords": ["paper mario"],
        "excludes": ["thousand", "color", "origami", "sticker"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokeemerald": {
        "keywords": ["emerald", "smaragd"],
        "excludes": [],
        "extensions": [".gba", ".bin", ".zip"],
        "target_name": "baserom.gba"
    },
    "pokered": {
        "keywords": ["pokemon - red", "pokemon red", "pokemon - rote", "pokemon rote edition", "pokered"],
        "excludes": ["fire", "feuer", "leaf", "blatt"],
        "extensions": [".gb", ".zip"],
        "target_name": "baserom.gb"
    },
    "pokefirered": {
        "keywords": ["firered", "feuerrot"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "sonic1-decomp": {
        "keywords": ["sonic the hedgehog (1991)", "sonic 1", "sonic the hedgehog 1"],
        "excludes": ["sonic 2", "sonic 3"],
        "extensions": [".bin", ".md", ".gen", ".zip"],
        "target_name": "Data.rsdk"
    },
    "sonic2-decomp": {
        "keywords": ["sonic the hedgehog 2", "sonic 2"],
        "excludes": ["sonic 1", "sonic 3"],
        "extensions": [".bin", ".md", ".gen", ".zip"],
        "target_name": "Data.rsdk"
    },
    "sonic-cd-decomp": {
        "keywords": ["sonic cd", "soniccd"],
        "excludes": [],
        "extensions": [".iso", ".bin", ".zip"],
        "target_name": "Data.rsdk"
    },
    "papermario-recut": {
        "keywords": ["paper mario"],
        "excludes": ["thousand", "color", "origami", "sticker"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "sf64-decomp": {
        "keywords": ["star fox 64", "starfox 64", "lylat wars", "lylatwars", "star fox"],
        "excludes": ["adventures", "assault", "command", "zero"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "goldeneye-007-decomp": {
        "keywords": ["goldeneye", "golden eye", "007 - goldeneye"],
        "excludes": ["rogue agent"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "mariokart64-decomp": {
        "keywords": ["mario kart 64", "mariokart 64"],
        "excludes": ["super circuit", "double dash", "wii", "7", "8"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "conker-decomp": {
        "keywords": ["conker's bad fur day", "conkers bad fur day", "conker"],
        "excludes": ["pocket"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "banjotooie-decomp": {
        "keywords": ["banjo-tooie", "banjo tooie", "banjotooie"],
        "excludes": ["nuts", "grunties"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "blastcorps-decomp": {
        "keywords": ["blast corps", "blastcorps"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "waverace64-decomp": {
        "keywords": ["wave race 64", "waverace 64", "wave race"],
        "excludes": ["blue storm"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "rayman2-decomp": {
        "keywords": ["rayman 2", "rayman2"],
        "excludes": ["revolution", "3", "hoodlum"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokecrystal": {
        "keywords": ["crystal", "kristall"],
        "excludes": [],
        "extensions": [".gbc", ".zip"],
        "target_name": "baserom.gbc"
    },
    "pokeyellow": {
        "keywords": ["yellow", "gelb", "special pikachu"],
        "excludes": [],
        "extensions": [".gb", ".zip"],
        "target_name": "baserom.gb"
    },
    "pokeruby": {
        "keywords": ["ruby", "rubin", "sapphire", "saphir"],
        "excludes": ["omega", "alpha"],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "pokeplatinum": {
        "keywords": ["platinum", "platin"],
        "excludes": [],
        "extensions": [".nds", ".zip"],
        "target_name": "baserom.nds"
    },
    "sm64ds-decomp": {
        "keywords": ["super mario 64 ds", "mario 64 ds", "sm64ds"],
        "excludes": [],
        "extensions": [".nds", ".zip"],
        "target_name": "baserom.nds"
    },
    "sonic-1-rsdk": {
        "keywords": ["sonic the hedgehog (1991)", "sonic 1"],
        "excludes": ["sonic 2", "sonic 3"],
        "extensions": [".rsdk", ".bin", ".zip"],
        "target_name": "Data.rsdk"
    },
    "sonic-2-rsdk": {
        "keywords": ["sonic the hedgehog 2", "sonic 2"],
        "excludes": ["sonic 1", "sonic 3"],
        "extensions": [".rsdk", ".bin", ".zip"],
        "target_name": "Data.rsdk"
    },
    "zelda3-pc": {
        "keywords": ["link to the past", "alttp", "zelda 3", "zelda3"],
        "excludes": [],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "zelda3.sfc"
    },
    "smw-pc": {
        "keywords": ["super mario world", "smw"],
        "excludes": ["world 2", "yoshi's island"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "smw.sfc"
    },
    "super-metroid-pc": {
        "keywords": ["super metroid"],
        "excludes": [],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "sm.sfc"
    },
    "sonic3air": {
        "keywords": ["sonic 3 & knuckles", "sonic and knuckles with sonic 3", "sonic3k", "sonic_knuckles_wsonic3", "sonic 3"],
        "excludes": [],
        "extensions": [".bin", ".gen", ".md", ".zip"],
        "target_name": "Sonic_Knuckles_wSonic3.bin"
    },
    "pokemon-stadium-recomp": {
        "keywords": ["pokemon stadium", "pokémon stadium"],
        "excludes": ["stadium 2"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokestadium-decomp": {
        "keywords": ["pokemon stadium", "pokémon stadium"],
        "excludes": ["stadium 2"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "kirby64-decomp": {
        "keywords": ["kirby 64", "kirby64"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokesnap-decomp": {
        "keywords": ["pokemon snap", "pokémon snap", "pokesnap"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "yoshisstory-decomp": {
        "keywords": ["yoshi's story", "yoshis story"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "ladx-decomp": {
        "keywords": ["link's awakening dx", "links awakening dx", "ladx"],
        "excludes": [],
        "extensions": [".gbc", ".zip"],
        "target_name": "baserom.gbc"
    },
    "oracles-decomp": {
        "keywords": ["oracle of ages", "oracle of seasons", "oracle"],
        "excludes": [],
        "extensions": [".gbc", ".zip"],
        "target_name": "baserom.gbc"
    },
    "pokegold-decomp": {
        "keywords": ["pokemon - gold", "pokemon gold", "pokemon - silber", "pokemon silver", "pokegold"],
        "excludes": ["heartgold", "soulsilver"],
        "extensions": [".gbc", ".gb", ".zip"],
        "target_name": "baserom.gbc"
    },
    "fe8-decomp": {
        "keywords": ["the sacred stones", "sacred stones"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "marioparty1-decomp": {
        "keywords": ["mario party"],
        "excludes": ["mario party 2", "mario party 3", "party 2", "party 3"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "marioparty3-decomp": {
        "keywords": ["mario party 3", "marioparty 3", "marioparty3"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "mischiefmakers-decomp": {
        "keywords": ["mischief makers", "mischiefmakers"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokediamond": {
        "keywords": ["diamond", "pearl", "diamant", "perl"],
        "excludes": ["brilliant", "shining"],
        "extensions": [".nds", ".zip"],
        "target_name": "baserom.nds"
    },
    "poketcg": {
        "keywords": ["trading card game", "pokemon tcg", "poketcg"],
        "excludes": [],
        "extensions": [".gbc", ".zip"],
        "target_name": "baserom.gbc"
    },
    "pokepinball": {
        "keywords": ["pokemon pinball", "pokepinball"],
        "excludes": ["ruby", "sapphire"],
        "extensions": [".gbc", ".zip"],
        "target_name": "baserom.gbc"
    },
    "fe6-decomp": {
        "keywords": ["binding blade", "fuuin no tsurugi"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "fe7-decomp": {
        "keywords": ["blazing blade", "the blazing blade", "fire emblem (usa)"],
        "excludes": ["sacred", "binding"],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "advancewars-decomp": {
        "keywords": ["advance wars"],
        "excludes": ["advance wars 2", "dual strike", "days of ruin"],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "advancewars2-decomp": {
        "keywords": ["advance wars 2", "black hole rising"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "aria-of-sorrow-decomp": {
        "keywords": ["aria of sorrow", "aria"],
        "excludes": ["dawn of sorrow"],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "metroid-fusion-decomp": {
        "keywords": ["metroid fusion", "fusion"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "metroid-zero-mission-decomp": {
        "keywords": ["zero mission", "zero-mission"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "smk-disasm": {
        "keywords": ["super mario kart"],
        "excludes": ["super circuit", "64"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "smk.sfc"
    },
    "chronotrigger-disasm": {
        "keywords": ["chrono trigger"],
        "excludes": ["cross"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "chronotrigger.sfc"
    },
    "smrpg-disasm": {
        "keywords": ["super mario rpg", "seven stars"],
        "excludes": [],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "smrpg.sfc"
    },
    "marioparty2-decomp": {
        "keywords": ["mario party 2", "marioparty 2", "marioparty2"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "castlevania64-decomp": {
        "keywords": ["castlevania 64", "legacy of darkness"],
        "excludes": ["symphony", "circle", "harmony", "aria", "dawn"],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "ogrebattle64-decomp": {
        "keywords": ["ogre battle 64", "ogrebattle 64"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pilotwings64-decomp": {
        "keywords": ["pilotwings 64", "pilot wings 64"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "pokestadium2-decomp": {
        "keywords": ["pokemon stadium 2", "pokémon stadium 2"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "chameleon-twist-decomp": {
        "keywords": ["chameleon twist"],
        "excludes": [],
        "extensions": [".z64", ".n64", ".v64", ".zip"],
        "target_name": "baserom.us.z64"
    },
    "mmx-disasm": {
        "keywords": ["mega man x", "megaman x"],
        "excludes": ["x2", "x3", "x4", "x5", "x6", "x7", "x8"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "mmx.sfc"
    },
    "mmx2-disasm": {
        "keywords": ["mega man x2", "megaman x2"],
        "excludes": [],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "mmx2.sfc"
    },
    "dkc1-disasm": {
        "keywords": ["donkey kong country"],
        "excludes": ["country 2", "country 3", "diddy", "dixie"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "dkc.sfc"
    },
    "dkc2-disasm": {
        "keywords": ["donkey kong country 2", "diddy's kong quest"],
        "excludes": ["country 3"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "dkc2.sfc"
    },
    "starfox-disasm": {
        "keywords": ["star fox", "starwing"],
        "excludes": ["64", "adventures", "assault"],
        "extensions": [".sfc", ".smc", ".zip"],
        "target_name": "starfox.sfc"
    },
    "mother3": {
        "keywords": ["mother 3", "mother3"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "goldensun-tla-decomp": {
        "keywords": ["the lost age", "lost age"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "cotm-decomp": {
        "keywords": ["circle of the moon"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "hod-decomp": {
        "keywords": ["harmony of dissonance"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "mmbn1-decomp": {
        "keywords": ["battle network", "rockman exe"],
        "excludes": ["battle network 2", "battle network 3", "battle network 4", "battle network 5", "battle network 6"],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "mmbn3-decomp": {
        "keywords": ["battle network 3"],
        "excludes": [],
        "extensions": [".gba", ".zip"],
        "target_name": "baserom.gba"
    },
    "pmd-sky-decomp": {
        "keywords": ["explorers of sky", "erkundungsteam himmel"],
        "excludes": ["time", "zeit", "darkness", "dunkelheit"],
        "extensions": [".nds", ".zip"],
        "target_name": "baserom.nds"
    }
}


class RomAutoMatcher:
    @staticmethod
    def get_candidate_rom_dirs() -> List[str]:
        """Returns detected potential ROM directories on user system."""
        found = set()
        std_dirs = [
            "/run/media/julian/HDD/Downloads/N64/Games",
            "/run/media/julian/HDD/Downloads/N64",
            os.path.expanduser("~/ROMs"),
            os.path.expanduser("~/roms"),
            os.path.expanduser("~/Emulation/roms"),
            os.path.expanduser("~/Games/ROMs"),
            os.path.expanduser("~/Downloads"),
        ]
        for p in std_dirs:
            if os.path.exists(p):
                found.add(p)

        for base in glob.glob("/run/media/*/*"):
            for sub in ["Downloads/N64/Games", "Downloads/N64", "ROMs", "roms", "Emulation/roms", "GC", "PS2", "PSX", "Wii"]:
                target = os.path.join(base, sub)
                if os.path.exists(target):
                    found.add(target)

        return sorted(list(found))

    @staticmethod
    def scan_for_rom(project_id: str, search_directory: str) -> Optional[str]:
        """Scans search_directory recursively for a matching ROM file."""
        if not search_directory or not os.path.exists(search_directory):
            return None

        rule = ROM_MATCH_RULES.get(project_id)
        if not rule:
            return None

        keywords = [kw.lower() for kw in rule["keywords"]]
        excludes = [ex.lower() for ex in rule.get("excludes", [])]
        extensions = [ext.lower() for ext in rule["extensions"]]

        # 1. First search direct non-zip ROM files
        for root, _, files in os.walk(search_directory):
            for file in files:
                lower = file.lower()
                if not any(lower.endswith(ext) for ext in extensions if ext != ".zip"):
                    continue
                if any(ex in lower for ex in excludes):
                    continue
                if any(kw in lower for kw in keywords):
                    return os.path.join(root, file)

        # 2. Then search zip archives
        for root, _, files in os.walk(search_directory):
            for file in files:
                lower = file.lower()
                if not lower.endswith(".zip"):
                    continue
                if any(ex in lower for ex in excludes):
                    continue
                if any(kw in lower for kw in keywords):
                    return os.path.join(root, file)

        return None

    @staticmethod
    def convert_n64_byteswap_if_needed(file_path: str) -> Tuple[bytes, str]:
        """
        Reads a ROM file, detects endianness, and converts byteswapped (.v64)
        or little-endian (.n64) ROMs into Big-Endian (.z64) format in milliseconds.
        """
        with open(file_path, "rb") as f:
            data = f.read()

        if len(data) < 4:
            return data, "Original"

        magic = data[:4]

        if magic == MAGIC_Z64_BIG_ENDIAN:
            return data, "Bereits Standard Big-Endian (.z64)"

        elif magic == MAGIC_V64_BYTESWAPPED:
            # 16-bit word swap (BADC -> ABCD)
            arr = array.array('H', data)
            arr.byteswap()
            return arr.tobytes(), "Automatisch von ByteSwapped (.v64) nach Big-Endian (.z64) konvertiert"

        elif magic == MAGIC_N64_LITTLE_ENDIAN:
            # 32-bit dword swap (DCBA -> ABCD)
            arr = array.array('I', data)
            arr.byteswap()
            return arr.tobytes(), "Automatisch von Little-Endian (.n64) nach Big-Endian (.z64) konvertiert"

        return data, "Original"

    @staticmethod
    def auto_import(project: GameProject, rom_dir: str, target_game_dir: str) -> Tuple[bool, str]:
        """
        Finds the matching ROM in rom_dir, extracts/converts if necessary,
        and saves it into target_game_dir with the required baserom name.
        """
        found_rom = RomAutoMatcher.scan_for_rom(project.id, rom_dir)
        if not found_rom:
            return False, f"Keine passende ROM für '{project.name}' im Verzeichnis '{rom_dir}' gefunden."

        rule = ROM_MATCH_RULES.get(project.id, {})
        target_name = rule.get("target_name")
        if not target_name and project.required_files:
            target_name = project.required_files[0]
        if not target_name:
            target_name = os.path.basename(found_rom)

        os.makedirs(target_game_dir, exist_ok=True)
        dest_path = os.path.join(target_game_dir, target_name)

        conversion_msg = ""
        source_file_to_process = found_rom
        temp_extracted = None

        try:
            # Handle .zip archive
            if found_rom.lower().endswith(".zip"):
                with zipfile.ZipFile(found_rom, 'r') as z:
                    cand_names = [n for n in z.namelist() if not n.endswith('/') and '__MACOSX' not in n]
                    valid_names = [n for n in cand_names if any(n.lower().endswith(e) for e in [".z64", ".v64", ".n64", ".gba", ".gb", ".bin", ".rsdk"])]
                    if valid_names:
                        chosen_entry = valid_names[0]
                    elif cand_names:
                        chosen_entry = cand_names[0]
                    else:
                        return False, "Das Zip-Archiv enthält keine gültigen Spieldateien."

                    extract_dir = os.path.join(target_game_dir, "_temp_rom_extract")
                    os.makedirs(extract_dir, exist_ok=True)
                    z.extract(chosen_entry, extract_dir)
                    source_file_to_process = os.path.join(extract_dir, chosen_entry)
                    temp_extracted = extract_dir
                    conversion_msg = f"Aus Archiv '{os.path.basename(found_rom)}' entpackt ({chosen_entry}). "

            # Check if N64 conversion is needed
            if target_name.endswith(".z64") or source_file_to_process.lower().endswith((".z64", ".v64", ".n64")):
                converted_bytes, status_note = RomAutoMatcher.convert_n64_byteswap_if_needed(source_file_to_process)
                with open(dest_path, "wb") as f_out:
                    f_out.write(converted_bytes)
                conversion_msg += status_note
            else:
                shutil.copy2(source_file_to_process, dest_path)
                conversion_msg += f"Als '{target_name}' eingerichtet"

            # Also create duplicate with original filename if different
            orig_dest = os.path.join(target_game_dir, os.path.basename(found_rom))
            if not orig_dest.lower().endswith(".zip") and orig_dest != dest_path and not os.path.exists(orig_dest):
                try:
                    shutil.copy2(dest_path, orig_dest)
                except Exception:
                    pass

            return True, f"Erfolg! Gefunden: '{os.path.basename(found_rom)}'\n{conversion_msg}\nZiel: {dest_path}"

        except Exception as e:
            logger.error(f"Error importing ROM: {e}")
            return False, f"Fehler beim Verarbeiten der ROM: {e}"
        finally:
            if temp_extracted and os.path.exists(temp_extracted):
                shutil.rmtree(temp_extracted, ignore_errors=True)
