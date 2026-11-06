"""Chargement et validation de la configuration (config/*.yaml + .env).

Les clés API éventuelles sont lues dans l'environnement (.env) et ne sont
jamais écrites dans les rapports ni dans les logs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from .errors import ConfigError

ROOT = Path(__file__).resolve().parents[2]
SECTIONS_VALIDES = {"tech", "ia", "claude"}


@dataclass(frozen=True)
class Category:
    id: str
    titre: str
    section: str
    requetes: list[str]
    mots_cles: list[str]


@dataclass(frozen=True)
class Config:
    root: Path
    langue: str
    tz: ZoneInfo
    fenetre_heures: int
    nb_actus_min: int
    nb_actus_max: int
    seuil_doublon_titre: float
    historique_jours: int
    dir_rapports: Path
    dir_donnees: Path
    dir_logs: Path
    categories: list[Category]
    sources_niveau_1: list[str]
    sources_niveau_2: list[str]
    pages_a_consulter: list[str] = field(default_factory=list)

    # --- Temps -----------------------------------------------------------
    def now(self) -> datetime:
        return datetime.now(self.tz)

    def window(self, now: datetime | None = None) -> tuple[datetime, datetime]:
        """(début, fin) de la période de veille, dans le fuseau configuré."""
        end = (now or self.now()).astimezone(self.tz)
        return end - timedelta(hours=self.fenetre_heures), end

    def category(self, cat_id: str) -> Category | None:
        return next((c for c in self.categories if c.id == cat_id), None)


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Fichier de configuration introuvable : {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML invalide dans {path.name} : {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} doit contenir un dictionnaire YAML")
    return data


def _load_dotenv(root: Path) -> None:
    """Charge .env s'il existe (facultatif : aucune clé n'est requise)."""
    env = root / ".env"
    if env.exists():
        try:
            from dotenv import load_dotenv
        except ImportError:  # dépendance facultative
            return
        load_dotenv(env, override=False)


def load_config(root: Path | None = None) -> Config:
    """Lit et valide toute la configuration. Lève ConfigError si invalide."""
    root = root or ROOT
    _load_dotenv(root)
    cfg_dir = root / "config"
    s = _read_yaml(cfg_dir / "settings.yaml")
    c = _read_yaml(cfg_dir / "categories.yaml")
    src = _read_yaml(cfg_dir / "sources.yaml")

    try:
        tz = ZoneInfo(s.get("fuseau_horaire", "Africa/Abidjan"))
    except ZoneInfoNotFoundError as exc:
        raise ConfigError(f"Fuseau horaire inconnu : {s.get('fuseau_horaire')}") from exc

    nb_min, nb_max = int(s.get("nb_actus_min", 5)), int(s.get("nb_actus_max", 10))
    if not 0 < nb_min <= nb_max:
        raise ConfigError("nb_actus_min doit être > 0 et <= nb_actus_max")
    fenetre = int(s.get("fenetre_heures", 24))
    if fenetre <= 0:
        raise ConfigError("fenetre_heures doit être positif")

    categories: list[Category] = []
    ids: set[str] = set()
    for raw in c.get("categories", []):
        missing = {"id", "titre", "section"} - set(raw)
        if missing:
            raise ConfigError(f"Catégorie incomplète {raw} : manque {sorted(missing)}")
        if raw["section"] not in SECTIONS_VALIDES:
            raise ConfigError(f"Catégorie {raw['id']} : section '{raw['section']}' invalide")
        if raw["id"] in ids:
            raise ConfigError(f"Identifiant de catégorie en double : {raw['id']}")
        ids.add(raw["id"])
        categories.append(Category(raw["id"], raw["titre"], raw["section"],
                                   list(raw.get("requetes", [])), [m.lower() for m in raw.get("mots_cles", [])]))
    if not categories:
        raise ConfigError("Aucune catégorie définie dans categories.yaml")

    dossiers = s.get("dossiers", {})
    return Config(
        root=root,
        langue=s.get("langue", "fr"),
        tz=tz,
        fenetre_heures=fenetre,
        nb_actus_min=nb_min,
        nb_actus_max=nb_max,
        seuil_doublon_titre=float(s.get("seuil_doublon_titre", 0.85)),
        historique_jours=int(s.get("historique_jours", 90)),
        dir_rapports=root / dossiers.get("rapports", "reports"),
        dir_donnees=root / dossiers.get("donnees", "data"),
        dir_logs=root / dossiers.get("logs", "logs"),
        categories=categories,
        sources_niveau_1=[d.lower() for d in src.get("niveau_1", [])],
        sources_niveau_2=[d.lower() for d in src.get("niveau_2", [])],
        pages_a_consulter=list(src.get("pages_a_consulter", [])),
    )


def secret(name: str) -> str | None:
    """Lit une clé API dans l'environnement. Ne jamais la journaliser."""
    value = os.environ.get(name)
    return value or None
