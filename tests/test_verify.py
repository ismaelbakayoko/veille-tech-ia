from datetime import date

from veille.collect import item_from_dict, normalize_url, trust_level
from veille.history import History
from veille.verify import verify

from conftest import NOW, make_item


def run(cfg, raws, history=None):
    return verify([item_from_dict(r) for r in raws], cfg, history, now=NOW)


def test_normalize_url():
    assert normalize_url("https://www.Anthropic.com/news/x/?utm_source=tw#top") == \
        "https://anthropic.com/news/x"


def test_niveaux_de_confiance(cfg):
    assert trust_level("https://www.anthropic.com/news", cfg) == 1
    assert trust_level("https://techcrunch.com/2026/11/05/x", cfg) == 2
    assert trust_level("https://blog-inconnu.example/x", cfg) == 3


def test_actu_valide_retenue(cfg):
    r = run(cfg, [make_item()])
    assert len(r.retenus) == 1 and not r.rejets
    assert r.retenus[0].extra["niveau_confiance"] == 1


def test_hors_periode_rejetee(cfg):
    r = run(cfg, [make_item(date_publication="2026-11-04T10:00:00Z")])
    assert "hors période" in r.rejets[0][1]


def test_date_jour_seul_acceptee_veille(cfg):
    r = run(cfg, [make_item(date_publication="2026-11-05")])
    assert len(r.retenus) == 1


def test_date_future_rejetee(cfg):
    r = run(cfg, [make_item(date_publication="2026-11-07")])
    assert r.rejets


def test_non_verifiee_rejetee(cfg):
    r = run(cfg, [make_item(verifie=False)])
    assert "non ouverte" in r.rejets[0][1]


def test_champs_manquants_et_lien(cfg):
    r = run(cfg, [make_item(url=""), make_item(url="http://anthropic.com/x", titre="Autre"),
                  make_item(categorie="inconnue", titre="Encore")])
    raisons = " ".join(x for _, x in r.rejets)
    assert "url" in raisons and "https" in raisons and "catégorie inconnue" in raisons


def test_date_illisible(cfg):
    r = run(cfg, [make_item(date_publication="hier")])
    assert "illisible" in r.rejets[0][1]


def test_doublon_garde_source_officielle(cfg):
    presse = make_item(url="https://techcrunch.com/2026/11/05/claude-code",
                       titre="Claude Code ajoute une nouvelle commande !", source="TechCrunch")
    officiel = make_item()
    r = run(cfg, [presse, officiel])
    assert len(r.retenus) == 1
    assert r.retenus[0].source == "Anthropic"
    assert "doublon" in r.rejets[0][1]


def test_meme_url_doublon(cfg):
    r = run(cfg, [make_item(), make_item(url="https://anthropic.com/news/exemple/?utm_source=x",
                                         titre="Titre totalement différent")])
    assert len(r.retenus) == 1


def test_deja_publiee_rejetee(cfg, tmp_path):
    h = History(tmp_path / "seen.json")
    h.add(normalize_url(make_item()["url"]), "x", date(2026, 11, 5))
    r = run(cfg, [make_item()], history=h)
    assert "déjà publiée" in r.rejets[0][1]


def test_historique_purge(tmp_path):
    h = History(tmp_path / "seen.json", keep_days=90)
    h.add("https://a.com/old", "old", date(2026, 1, 1))
    h.add("https://a.com/new", "new", date(2026, 11, 1))
    assert h.prune(date(2026, 11, 6)) == 1
    h.save()
    assert len(History(tmp_path / "seen.json")) == 1


def test_historique_corrompu(tmp_path):
    p = tmp_path / "seen.json"
    p.write_text("{pas du json", encoding="utf-8")
    assert len(History(p)) == 0
