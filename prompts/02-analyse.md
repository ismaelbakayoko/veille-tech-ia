# Étape 4 — Analyse, sélection et rédaction

Travaille **uniquement** à partir de `data/retenus.json`. Toute URL d'actualité citée dans
`tech`, `ia` ou `claude_code.nouveautes` doit venir de ce fichier (sinon `report` refuse).

## Sélection (5 à 10 actus au total)

Classe chaque actu selon son intérêt pour un développeur web / mobile / backend :
1. Impact direct sur le code ou les outils (version majeure, breaking change, faille, nouvelle API).
2. Nouveauté IA utilisable par un développeur (modèle, API, agent, MCP, outil de code).
3. Tendance de fond des grandes entreprises tech.

Équilibre les rubriques : les catégories `section: tech` vont dans `tech`, `section: ia` dans
`ia`, `section: claude` dans `claude_code.nouveautes`. Une actu n'apparaît qu'une seule fois.

## Rédaction (français clair, ton professionnel, phrases courtes)

- `resume_executif` : les 3 infos les plus importantes, une phrase chacune.
- `tech[].importance_dev` : concrètement, que change cette actu pour un développeur ?
- `ia[]` : `entreprise`, `fonctionnalites` (ce qui est nouveau), `applications` (cas d'usage concrets).
- `claude_code` :
  - `nouveautes` : annonces vérifiées des dernières 24 h (peut être vide).
  - `bonnes_pratiques`, `outils_integrations`, `exemple`, `ecosysteme` : contenu pédagogique
    utile au quotidien. Il peut être intemporel, mais doit s'appuyer sur la documentation
    officielle (docs.claude.com, anthropic.com, dépôt anthropics/claude-code) : mets les
    pages utilisées dans `liens`. Varie les sujets d'un jour à l'autre (regarde les rapports
    précédents dans `reports/`).
- `a_retenir` : 5 points maximum, actionnables.
- `outil` : un outil réel et utile (dev ou IA), avec son **lien officiel**, différent de ceux
  des rapports précédents.
- `defi` : un petit exercice pratique (30-60 min) lié à l'actualité du jour si possible,
  en tournant entre Flutter, Spring Boot, React/Next.js, SQL, IA/API. Donne `niveau`,
  `duree`, `technologies`, un `enonce` précis et 2-3 `indices`.
- `note` : à remplir si la journée est calme ou si une catégorie n'a rien donné.
