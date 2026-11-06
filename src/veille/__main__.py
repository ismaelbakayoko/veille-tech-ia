"""Interface en ligne de commande.

    python -m veille init                 # prépare l'exécution, affiche la période et les requêtes
    python -m veille verify               # data/candidats.json -> data/retenus.json + data/rejets.json
    python -m veille report               # data/analyse.json -> reports/rapport-YYYY-MM-DD.md
    python -m veille check-config         # valide la configuration

Codes de sortie : 0 = succès, 1 = erreur métier (message explicite), 2 = erreur inattendue.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .collect import load_items, save_items
from .config import load_config
from .errors import VeilleError
from .history import History
from .logger import setup_logging
from .report import build_email, build_report
from .verify import verify


def cmd_init(cfg, args) -> int:
    start, end = cfg.window()
    for d in (cfg.dir_rapports, cfg.dir_donnees, cfg.dir_logs):
        d.mkdir(parents=True, exist_ok=True)
    print(json.dumps({
        "date_du_rapport": end.date().isoformat(),
        "fichier_rapport": f"{cfg.dir_rapports.name}/rapport-{end.date().isoformat()}.md",
        "periode_debut": start.isoformat(timespec="minutes"),
        "periode_fin": end.isoformat(timespec="minutes"),
        "fuseau": cfg.tz.key,
        "nb_actus": [cfg.nb_actus_min, cfg.nb_actus_max],
        "pages_a_consulter": cfg.pages_a_consulter,
        "categories": [{"id": c.id, "titre": c.titre, "section": c.section, "requetes": c.requetes}
                       for c in cfg.categories],
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(cfg, args) -> int:
    items = load_items(Path(args.input))
    history = History(cfg.dir_donnees / "seen.json", cfg.historique_jours)
    result = verify(items, cfg, history)
    save_items(result.retenus, cfg.dir_donnees / "retenus.json")
    (cfg.dir_donnees / "rejets.json").write_text(json.dumps(
        [{"titre": i.titre, "url": i.url, "raison": r} for i, r in result.rejets],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {len(result.retenus)} actualité(s) retenue(s), {len(result.rejets)} rejetée(s)")
    for i, r in result.rejets:
        print(f"  ✘ {i.titre[:70] or i.url} — {r}")
    return 0


def cmd_report(cfg, args) -> int:
    history = History(cfg.dir_donnees / "seen.json", cfg.historique_jours)
    out = build_report(cfg, Path(args.input), cfg.dir_donnees / "retenus.json", history)
    print(f"✔ Rapport généré : {out.relative_to(cfg.root)}")
    return 0


def cmd_email(cfg, args) -> int:
    day = cfg.now().date().isoformat()
    report = Path(args.input) if args.input else cfg.dir_rapports / f"rapport-{day}.md"
    out = build_email(cfg, report)
    print(f"✔ Version e-mail : {out.relative_to(cfg.root)}")
    return 0


def cmd_check(cfg, args) -> int:
    print(f"✔ Configuration valide : {len(cfg.categories)} catégories, "
          f"{len(cfg.sources_niveau_1)} sources officielles, fuseau {cfg.tz.key}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="veille", description="Veille tech & IA quotidienne")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="prépare l'exécution du jour")
    p = sub.add_parser("verify", help="vérifie et dédoublonne les actus collectées")
    p.add_argument("input", nargs="?", default="data/candidats.json")
    p = sub.add_parser("report", help="génère le rapport Markdown")
    p.add_argument("input", nargs="?", default="data/analyse.json")
    p = sub.add_parser("email", help="convertit le rapport du jour en HTML pour l'e-mail")
    p.add_argument("input", nargs="?", default=None)
    sub.add_parser("check-config", help="valide la configuration")
    args = parser.parse_args(argv)

    try:
        cfg = load_config()
        log = setup_logging(cfg.dir_logs, cfg.now().date().isoformat())
        log.debug("Commande : %s", args.cmd)
        handler = {"init": cmd_init, "verify": cmd_verify, "report": cmd_report,
                   "email": cmd_email, "check-config": cmd_check}[args.cmd]
        return handler(cfg, args)
    except VeilleError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # erreur imprévue : trace complète dans les logs
        import logging
        logging.getLogger("veille").exception("Erreur inattendue")
        print(f"ERREUR INATTENDUE : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
