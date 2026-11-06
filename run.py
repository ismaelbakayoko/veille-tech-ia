#!/usr/bin/env python3
"""Point d'entrée : `python3 run.py <commande>` (init | verify | report | check-config)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from veille.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
