#!/usr/bin/env python3
"""Entry point for Recomp Center."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recomp_center.app import main

if __name__ == "__main__":
    main()
