"""Mémoire des actualités déjà publiées (data/seen.json).

Empêche qu'une même actu réapparaisse d'un jour à l'autre. Format :
    {"https://url-normalisee": {"date": "2026-11-06", "titre": "..."}}
Les entrées plus anciennes que `historique_jours` sont purgées.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .logger import get_logger

log = get_logger("history")


class History:
    def __init__(self, path: Path, keep_days: int = 90):
        self.path = path
        self.keep_days = keep_days
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Fichier corrompu : on repart à zéro sans bloquer la veille.
            log.warning("seen.json illisible, historique réinitialisé")
            self._data = {}

    def seen(self, url_norm: str) -> bool:
        return url_norm in self._data

    def titles(self) -> list[str]:
        return [v.get("titre", "") for v in self._data.values()]

    def add(self, url_norm: str, titre: str, day: date) -> None:
        self._data[url_norm] = {"date": day.isoformat(), "titre": titre}

    def prune(self, today: date) -> int:
        limit = today - timedelta(days=self.keep_days)
        old = [u for u, v in self._data.items() if date.fromisoformat(v["date"]) < limit]
        for u in old:
            del self._data[u]
        return len(old)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True),
                             encoding="utf-8")

    def __len__(self) -> int:
        return len(self._data)
