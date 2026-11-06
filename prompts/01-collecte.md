# Étape 2 — Collecte et vérification des sources

## Méthode

> ⚠️ **WebFetch n'ouvre que des URL apparues dans un résultat de WebSearch.** Une URL tapée
> directement (même officielle, ex. anthropic.com/news) est refusée. Toujours chercher
> d'abord, puis ouvrir un lien des résultats.

1. **Agrégateurs datés du jour** (meilleur rendement, testé le 6/11/2026) : cherche
   `"<date du jour en anglais>" AI news` et `tech news roundup <date>` en mode `extended`
   (ex. digests The Neuron, AI Weekly, Tech Startups). Ouvre-les pour récupérer la liste des
   annonces du jour, puis cherche chaque annonce pour atteindre sa source originale.
2. **Recherches par catégorie** : pour chaque catégorie, lance ses `requetes` (WebSearch,
   toutes celles d'une catégorie dans le même tour) en ajoutant le mois et l'année
   (`<requête> November 2026`). Les sources officielles de `pages_a_consulter` se trouvent
   via une recherche du type `site officiel + sujet`.
3. **Remonter à la source** : si une piste vient de la presse, cherche l'annonce officielle
   (blog de l'éditeur, changelog, release GitHub) et cite celle-ci.
4. **Vérifier chaque piste retenue** : ouvre la page (WebFetch) et confirme
   - la **date de publication** affichée sur la page ;
   - que le contenu correspond bien au titre (pas une rumeur, pas un ancien article remonté).
   Si la date n'est pas lisible ou si la page ne s'ouvre pas : `"verifie": false`.

## Ce qui compte comme « actualité »

✅ Nouvelle version, nouvelle fonctionnalité, nouveau modèle, annonce officielle, faille de
sécurité importante, changement de prix/licence/API, dépréciation, acquisition majeure.
❌ Tutoriels génériques, articles d'opinion, rumeurs, contenus sponsorisés, « top 10 »,
annonces de plus de 24 h republiées.

## Format de `data/candidats.json`

Liste d'objets — garde 15 à 30 pistes, `verify` fera le tri :

```json
[
  {
    "titre": "Titre en français, précis",
    "url": "https://source-originale/...",
    "source": "Nom lisible (ex. Anthropic, GitHub Blog, TechCrunch)",
    "date_publication": "2026-11-06",
    "categorie": "claude",
    "resume": "2-3 phrases factuelles en français, d'après la page lue.",
    "verifie": true
  }
]
```

- `date_publication` : `YYYY-MM-DD`, ou `YYYY-MM-DDTHH:MM:SSZ` si l'heure est connue.
- `categorie` : un `id` de `config/categories.yaml`.
