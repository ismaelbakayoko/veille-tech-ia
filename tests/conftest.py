import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from veille.config import load_config  # noqa: E402

NOW = datetime(2026, 11, 6, 6, 45, tzinfo=ZoneInfo("Africa/Abidjan"))


@pytest.fixture
def project(tmp_path):
    """Copie isolée du projet (config + templates) pour chaque test."""
    for d in ("config", "templates"):
        shutil.copytree(ROOT / d, tmp_path / d)
    return tmp_path


@pytest.fixture
def cfg(project):
    return load_config(project)


def make_item(**kw):
    base = {
        "titre": "Claude Code ajoute une nouvelle commande",
        "url": "https://www.anthropic.com/news/exemple",
        "source": "Anthropic",
        "date_publication": "2026-11-05T18:00:00Z",
        "categorie": "claude",
        "resume": "Résumé de test.",
        "verifie": True,
    }
    base.update(kw)
    return base
