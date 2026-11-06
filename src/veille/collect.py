"""Module de collecte : modèle d'une actualité et normalisation des données.

Claude enregistre ce qu'il trouve (recherche web + pages officielles) dans
data/candidats.json, sous la forme d'une liste d'objets :

    {
      "titre": "...",                  # obligatoire
      "url": "https://...",            # obligatoire, lien vers la source originale
      "source": "Anthropic",           # nom lisible de la source
      "date_publication": "2026-11-06" # ou "2026-11-06T14:30:00Z" ; obligatoire
      "categorie": "claude",           # id d'une catégorie de categories.yaml
      "resume": "...",                 # 2-3 phrases, en français
      "verifie": true                  # true seulement si la page a été ouverte
    }                                   # et la date confirmée sur la page

Ce module transforme ces objets en `Item` typés, normalise les URL et
calcule le niveau de confiance de la source.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .config import Config
from .errors import DataError

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_", "ref", "source")


@dataclass
class Item:
    titre: str
    url: str
    source: str
    date_publication: str
    categorie: str
    resume: str = ""
    verifie: bool = False
    extra: dict = field(default_factory=dict)  # champs libres conservés tels quels

    # Calculés
    @property
    def url_norm(self) -> str:
        return normalize_url(self.url)

    @property
    def domaine(self) -> str:
        return domain_of(self.url)

    def to_dict(self) -> dict:
        d = asdict(self)
        extra = d.pop("extra")
        return {**extra, **d}


def normalize_url(url: str) -> str:
    """URL canonique pour le dédoublonnage (sans suivi, ancre ni / final)."""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query)
             if not k.lower().startswith(_TRACKING_PREFIXES)]
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, urlencode(query), ""))


def domain_of(url: str) -> str:
    return urlsplit(url.strip()).netloc.lower().removeprefix("www.")


def trust_level(url: str, cfg: Config) -> int:
    """1 = officielle, 2 = presse reconnue, 3 = autre."""
    host = domain_of(url)
    full = host + urlsplit(url).path.lower()

    def match(domains: list[str]) -> bool:
        return any(host == d or host.endswith("." + d) or full.startswith(d) for d in domains)

    if match(cfg.sources_niveau_1):
        return 1
    if match(cfg.sources_niveau_2):
        return 2
    return 3


def parse_date(value: str) -> tuple[datetime | date, bool]:
    """Analyse une date ISO. Renvoie (valeur, a_une_heure).

    Accepte 'YYYY-MM-DD' (précision au jour) ou un datetime ISO 8601.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("date vide")
    v = value.strip().replace("Z", "+00:00")
    if len(v) == 10:
        return date.fromisoformat(v), False
    return datetime.fromisoformat(v), True


_KNOWN = {"titre", "url", "source", "date_publication", "categorie", "resume", "verifie"}


def item_from_dict(raw: dict) -> Item:
    if not isinstance(raw, dict):
        raise DataError(f"Entrée invalide (objet attendu) : {raw!r}")
    return Item(
        titre=str(raw.get("titre", "")).strip(),
        url=str(raw.get("url", "")).strip(),
        source=str(raw.get("source", "")).strip(),
        date_publication=str(raw.get("date_publication", "")).strip(),
        categorie=str(raw.get("categorie", "")).strip(),
        resume=str(raw.get("resume", "")).strip(),
        verifie=bool(raw.get("verifie", False)),
        extra={k: v for k, v in raw.items() if k not in _KNOWN},
    )


def load_items(path: Path) -> list[Item]:
    """Charge data/candidats.json (liste d'objets)."""
    if not path.exists():
        raise DataError(f"Fichier introuvable : {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(f"JSON invalide dans {path.name} : {exc}") from exc
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise DataError(f"{path.name} doit contenir une liste d'actualités")
    return [item_from_dict(r) for r in data]


def save_items(items: list[Item], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([i.to_dict() for i in items], ensure_ascii=False, indent=2),
                    encoding="utf-8")
