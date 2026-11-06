"""Module de génération du rapport quotidien.

Entrée : data/analyse.json, rédigé par Claude à partir des actus vérifiées
(data/retenus.json). Sortie : reports/rapport-YYYY-MM-DD.md + reports/INDEX.md.

Garde-fou anti-invention : toute actualité citée dans les rubriques Tech, IA
et Focus Claude Code doit avoir une URL présente dans data/retenus.json,
c'est-à-dire passée par la vérification. Sinon le rapport est refusé.

Format de data/analyse.json :
{
  "resume_executif": ["...", "...", "..."],            # les 3 infos majeures
  "tech": [{"titre", "resume", "date_publication", "source", "url",
            "importance_dev", "categorie"}],
  "ia":   [{"titre", "entreprise", "fonctionnalites", "applications",
            "date_publication", "source", "url", "categorie"}],
  "claude_code": {
      "nouveautes": [{"titre", "resume", "date_publication", "source", "url"}],
      "bonnes_pratiques": "...", "outils_integrations": "...",
      "exemple": "...", "ecosysteme": "...",
      "liens": [{"titre", "url"}]                       # docs officielles citées
  },
  "a_retenir": ["...", ... 5 max],
  "outil": {"nom", "utilite", "pourquoi", "lien"},
  "defi":  {"titre", "niveau", "duree", "technologies", "enonce", "indices": [...]},
  "note": "facultatif, ex. journée calme"
}
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .collect import normalize_url, parse_date
from .config import Config
from .errors import DataError, ReportError
from .history import History
from .logger import get_logger

log = get_logger("report")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def date_fr(value: str | date | datetime, with_weekday: bool = False) -> str:
    """'2026-11-06' -> '6 novembre 2026' (ou 'vendredi 6 novembre 2026')."""
    if isinstance(value, str):
        value, _ = parse_date(value)
    d = value.date() if isinstance(value, datetime) else value
    txt = f"{d.day} {MOIS[d.month - 1]} {d.year}"
    return f"{JOURS[d.weekday()]} {txt}" if with_weekday else txt


def load_analysis(path: Path) -> dict:
    if not path.exists():
        raise DataError(f"Fichier d'analyse introuvable : {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(f"JSON invalide dans {path.name} : {exc}") from exc
    if not isinstance(data, dict):
        raise DataError("analyse.json doit contenir un objet")
    data.setdefault("tech", [])
    data.setdefault("ia", [])
    data.setdefault("claude_code", {})
    data["claude_code"].setdefault("nouveautes", [])
    data["claude_code"].setdefault("liens", [])
    for key in ("bonnes_pratiques", "outils_integrations", "exemple", "ecosysteme"):
        data["claude_code"].setdefault(key, "")
    data.setdefault("outil", {})
    data["outil"].setdefault("pourquoi", "")
    data.setdefault("defi", {})
    for key in ("niveau", "duree", "technologies"):
        data["defi"].setdefault(key, "")
    data["defi"].setdefault("indices", [])
    data.setdefault("a_retenir", [])
    data.setdefault("note", "")
    return data


def news_items(analysis: dict) -> list[dict]:
    return analysis["tech"] + analysis["ia"] + analysis["claude_code"]["nouveautes"]


def validate(analysis: dict, verified_urls: set[str], cfg: Config) -> list[str]:
    """Vérifie le contenu. Lève ReportError si bloquant, renvoie les avertissements."""
    errors, warnings = [], []
    seen: set[str] = set()

    for item in news_items(analysis):
        label = item.get("titre", "?")[:60]
        for key in ("titre", "url", "source", "date_publication"):
            if not item.get(key):
                errors.append(f"« {label} » : champ {key} manquant")
        url = item.get("url", "")
        if url:
            if not url.startswith("https://"):
                errors.append(f"« {label} » : lien non https")
            norm = normalize_url(url)
            if norm not in verified_urls:
                errors.append(f"« {label} » : URL absente des actus vérifiées ({url})")
            if norm in seen:
                errors.append(f"« {label} » : actualité en double dans le rapport")
            seen.add(norm)

    for item in analysis["tech"]:
        if not item.get("importance_dev"):
            errors.append(f"Tech « {item.get('titre', '?')[:60]} » : importance_dev manquante")
    for item in analysis["ia"]:
        for key in ("entreprise", "fonctionnalites", "applications"):
            if not item.get(key):
                errors.append(f"IA « {item.get('titre', '?')[:60]} » : {key} manquant")

    nb_exec = len(analysis.get("resume_executif", []))
    if not 1 <= nb_exec <= 3:
        errors.append(f"Résumé exécutif : 1 à 3 points attendus ({nb_exec})")
    if not 1 <= len(analysis["a_retenir"]) <= 5:
        errors.append("« Ce que je dois retenir » : 1 à 5 points attendus")

    outil = analysis.get("outil") or {}
    if not (outil.get("nom") and outil.get("utilite") and str(outil.get("lien", "")).startswith("https://")):
        errors.append("Outil à découvrir : nom, utilité et lien https requis")
    defi = analysis.get("defi") or {}
    if not (defi.get("titre") and defi.get("enonce")):
        errors.append("Défi technique : titre et énoncé requis")
    for lien in analysis["claude_code"]["liens"]:
        if not str(lien.get("url", "")).startswith("https://"):
            errors.append(f"Focus Claude Code : lien invalide {lien}")

    total = len(news_items(analysis))
    if total > cfg.nb_actus_max:
        errors.append(f"{total} actualités : maximum {cfg.nb_actus_max}")
    if total < cfg.nb_actus_min:
        warnings.append(f"Seulement {total} actualité(s) vérifiée(s) : journée calme")

    if errors:
        raise ReportError("Rapport refusé :\n  - " + "\n  - ".join(errors))
    for w in warnings:
        log.warning(w)
    return warnings


def render(analysis: dict, cfg: Config, day: date, generated_at: datetime) -> str:
    env = Environment(loader=FileSystemLoader(cfg.root / "templates"),
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                      keep_trailing_newline=True)
    env.filters["date_fr"] = date_fr
    start, end = cfg.window(generated_at)
    return env.get_template("rapport.md.j2").render(
        a=analysis,
        jour=date_fr(day, with_weekday=True),
        periode=f"{start:%d/%m/%Y %H:%M} → {end:%d/%m/%Y %H:%M} ({cfg.tz.key})",
        genere_le=f"{generated_at:%d/%m/%Y à %H:%M}",
        nb_actus=len(news_items(analysis)),
    )


def write_index(cfg: Config) -> Path:
    """Régénère reports/INDEX.md : liste de tous les rapports, du plus récent au plus ancien."""
    reports = sorted(cfg.dir_rapports.glob("rapport-*.md"), reverse=True)
    lines = ["# Historique des rapports de veille", ""]
    for p in reports:
        day = p.stem.removeprefix("rapport-")
        try:
            label = date_fr(day, with_weekday=True)
        except ValueError:
            label = day
        lines.append(f"- [{label}]({p.name})")
    path = cfg.dir_rapports / "INDEX.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


EMAIL_CSS = (
    "body{font-family:Arial,Helvetica,sans-serif;line-height:1.55;color:#1f2933;max-width:760px;"
    "margin:auto;padding:16px}h1{font-size:22px;color:#0b3d91}h2{font-size:18px;color:#0b3d91;"
    "border-bottom:2px solid #e4e7eb;padding-bottom:4px;margin-top:28px}h3{font-size:16px}"
    "blockquote{background:#f5f7fa;border-left:4px solid #0b3d91;margin:0;padding:8px 12px;"
    "color:#52606d}code{background:#f0f4f8;padding:1px 4px;border-radius:3px}a{color:#0b5fff}"
    "hr{border:none;border-top:1px solid #e4e7eb}"
)


def to_email_html(markdown_text: str) -> str:
    """Convertit le rapport Markdown en HTML autonome pour l'e-mail."""
    import markdown  # import local : dépendance utile seulement pour l'e-mail

    body = markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])
    return (f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
            f"<style>{EMAIL_CSS}</style></head><body>{body}</body></html>")


def build_email(cfg: Config, report_path: Path) -> Path:
    """Écrit data/email.html (non versionné) à partir du rapport du jour."""
    if not report_path.exists():
        raise DataError(f"Rapport introuvable : {report_path}")
    out = cfg.dir_donnees / "email.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_email_html(report_path.read_text(encoding="utf-8")), encoding="utf-8")
    log.info("Version e-mail écrite : %s", out.name)
    return out


def build_report(cfg: Config, analysis_path: Path, verified_path: Path,
                 history: History, now: datetime | None = None) -> Path:
    """Valide l'analyse, écrit le rapport du jour, met à jour l'historique."""
    now = (now or cfg.now()).astimezone(cfg.tz)
    day = now.date()
    analysis = load_analysis(analysis_path)

    if not verified_path.exists():
        raise DataError(f"{verified_path.name} introuvable : lancer d'abord `verify`")
    verified = json.loads(verified_path.read_text(encoding="utf-8"))
    verified_urls = {normalize_url(i["url"]) for i in verified}

    validate(analysis, verified_urls, cfg)
    content = render(analysis, cfg, day, now)

    cfg.dir_rapports.mkdir(parents=True, exist_ok=True)
    out = cfg.dir_rapports / f"rapport-{day.isoformat()}.md"
    if out.exists():
        log.warning("%s existe déjà : remplacé par la nouvelle version", out.name)
    out.write_text(content, encoding="utf-8")

    for item in news_items(analysis):
        history.add(normalize_url(item["url"]), item["titre"], day)
    pruned = history.prune(day)
    history.save()
    write_index(cfg)
    log.info("Rapport écrit : %s (%d actus, historique %d, purgé %d)",
             out.name, len(news_items(analysis)), len(history), pruned)
    return out
