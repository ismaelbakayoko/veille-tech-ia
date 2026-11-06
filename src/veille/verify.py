"""Module de vérification des sources.

Règles appliquées à chaque actualité candidate (une règle échouée = rejet) :
  1. Champs obligatoires présents (titre, url, source, date, catégorie).
  2. Lien en https:// valide.
  3. Catégorie connue (categories.yaml).
  4. Page effectivement ouverte et date confirmée (`verifie: true`).
  5. Date de publication dans la période de veille (dernières N heures).
  6. Pas déjà publiée dans un rapport précédent (historique).
  7. Pas de doublon dans la collecte du jour (même URL ou titre très proche) ;
     en cas de doublon, on garde la source la plus fiable.
Les sources hors des listes reconnues (niveau 3) sont acceptées mais signalées.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from difflib import SequenceMatcher
from urllib.parse import urlsplit

from .collect import Item, parse_date, trust_level
from .config import Config
from .history import History
from .logger import get_logger

log = get_logger("verify")


@dataclass
class VerifyResult:
    retenus: list[Item] = field(default_factory=list)
    rejets: list[tuple[Item, str]] = field(default_factory=list)

    def reject(self, item: Item, reason: str) -> None:
        self.rejets.append((item, reason))
        log.info("Rejeté : %s — %s", item.titre[:80] or item.url, reason)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def in_window(value: str, start: datetime, end: datetime) -> bool:
    """La date est-elle dans [start, end] ? Une date sans heure est jugée au jour."""
    parsed, has_time = parse_date(value)
    if has_time:
        dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=end.tzinfo)
        return start <= dt <= end
    assert isinstance(parsed, date)
    return start.date() <= parsed <= end.date()


def check_item(item: Item, cfg: Config, start: datetime, end: datetime) -> str | None:
    """Renvoie la raison du rejet, ou None si l'actu est valide."""
    for name in ("titre", "url", "source", "date_publication", "categorie"):
        if not getattr(item, name):
            return f"champ obligatoire manquant : {name}"
    parts = urlsplit(item.url)
    if parts.scheme != "https" or not parts.netloc:
        return "lien invalide (https:// requis)"
    if cfg.category(item.categorie) is None:
        return f"catégorie inconnue : {item.categorie}"
    if not item.verifie:
        return "page non ouverte / date non confirmée sur la source"
    try:
        if not in_window(item.date_publication, start, end):
            return f"hors période ({item.date_publication})"
    except ValueError:
        return f"date illisible : {item.date_publication!r}"
    return None


def _quality(item: Item, cfg: Config) -> tuple:
    """Clé de tri : meilleure source d'abord, puis résumé le plus riche."""
    return (trust_level(item.url, cfg), -len(item.resume))


def verify(items: list[Item], cfg: Config, history: History | None = None,
           now: datetime | None = None) -> VerifyResult:
    start, end = cfg.window(now)
    log.info("Période de veille : %s -> %s", start.isoformat(timespec="minutes"),
             end.isoformat(timespec="minutes"))
    result = VerifyResult()

    valid: list[Item] = []
    for item in items:
        reason = check_item(item, cfg, start, end)
        if reason is None and history is not None and history.seen(item.url_norm):
            reason = "déjà publiée dans un rapport précédent"
        if reason:
            result.reject(item, reason)
        else:
            valid.append(item)

    # Dédoublonnage : on parcourt de la meilleure à la moins bonne source.
    for item in sorted(valid, key=lambda i: _quality(i, cfg)):
        dup = next((k for k in result.retenus
                    if k.url_norm == item.url_norm
                    or _similar(k.titre, item.titre) >= cfg.seuil_doublon_titre), None)
        if dup:
            result.reject(item, f"doublon de « {dup.titre[:60]} »")
            continue
        level = trust_level(item.url, cfg)
        item.extra["niveau_confiance"] = level
        if level == 3:
            log.warning("Source hors liste reconnue (à surveiller) : %s", item.domaine)
        result.retenus.append(item)

    log.info("Vérification : %d retenues, %d rejetées", len(result.retenus), len(result.rejets))
    return result
