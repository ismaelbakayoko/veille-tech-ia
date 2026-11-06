# veille-tech-ia

Assistant autonome de veille technologique et IA : chaque matin, un rapport en français
sur l'actualité des dernières 24 heures (développement web, mobile, backend, bases de
données, cloud, cybersécurité, IA, Claude Code).

## Fonctionnement

Une **tâche planifiée Claude** (cloud) s'exécute tous les jours à **6 h 45 (Africa/Abidjan)**,
même ordinateur éteint. Elle suit la procédure de [`CLAUDE.md`](CLAUDE.md) :

```
init ─► collecte (recherche web + blogs officiels) ─► verify ─► analyse ─► report ─► git push + e-mail
```

| Module | Rôle |
|---|---|
| `src/veille/config.py` | Chargement et validation de `config/*.yaml` et `.env` |
| `src/veille/collect.py` | Modèle d'une actualité, normalisation des URL, niveau de confiance des sources |
| `src/veille/verify.py` | Période de 24 h, champs obligatoires, page vérifiée, doublons, déjà publié |
| `src/veille/history.py` | Mémoire anti-doublons entre les jours (`data/seen.json`, 90 jours) |
| `src/veille/report.py` | Validation anti-invention + rendu du rapport + `reports/INDEX.md` |
| `src/veille/logger.py` | Journaux dans `logs/veille-YYYY-MM-DD.log` |

**Garde-fou anti-invention :** le rapport est refusé si une actualité citée n'a pas été
vérifiée (URL absente de `data/retenus.json`), si un champ obligatoire manque ou si une
actu est en double.

## Utilisation manuelle

```bash
pip install -r requirements.txt
python3 run.py check-config
python3 run.py init
python3 run.py verify          # lit data/candidats.json
python3 run.py report          # lit data/analyse.json
python3 -m pytest -q           # tests
```

## Personnaliser

- **Ajouter une catégorie :** ajouter un bloc dans `config/categories.yaml` (id, titre, section, requêtes).
- **Ajouter une source reconnue :** ajouter le domaine dans `config/sources.yaml`.
- **Changer la période ou le nombre d'actus :** `config/settings.yaml`.
- **Modifier l'heure :** l'heure est dans la tâche planifiée, pas dans le code. Demander à
  Claude « passe la tâche veille-tech-ia à 7 h 30 », ou la modifier dans la liste des tâches
  planifiées de claude.ai.

## Clés API

Aucune clé n'est nécessaire. Si une API est ajoutée plus tard, la placer dans `.env`
(copié depuis `.env.example`, ignoré par git) et la lire avec `veille.config.secret()`.

## Rapports

Tous les rapports sont dans [`reports/`](reports/) — index : [`reports/INDEX.md`](reports/INDEX.md).
