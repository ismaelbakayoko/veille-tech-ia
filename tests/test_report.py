import json

import pytest

from veille.errors import ReportError
from veille.history import History
from veille.report import build_report, date_fr

from conftest import NOW, make_item

URL_TECH = "https://nextjs.org/blog/exemple"
URL_IA = "https://openai.com/index/exemple"
URL_CC = "https://www.anthropic.com/news/exemple"


def analysis(**over):
    a = {
        "resume_executif": ["Point 1", "Point 2", "Point 3"],
        "tech": [{"titre": "Next.js sort une version", "resume": "R", "date_publication": "2026-11-05",
                  "source": "Vercel", "url": URL_TECH, "importance_dev": "Important", "categorie": "web"}],
        "ia": [{"titre": "OpenAI annonce X", "entreprise": "OpenAI", "fonctionnalites": "F",
                "applications": "A", "date_publication": "2026-11-05", "source": "OpenAI", "url": URL_IA}],
        "claude_code": {"nouveautes": [{"titre": "Nouvelle commande", "resume": "R",
                                        "date_publication": "2026-11-05", "source": "Anthropic",
                                        "url": URL_CC}],
                        "bonnes_pratiques": "Utiliser CLAUDE.md", "liens": [
                            {"titre": "Docs", "url": "https://docs.claude.com/fr/docs/claude-code/overview"}]},
        "a_retenir": ["a", "b", "c", "d", "e"],
        "outil": {"nom": "Outil", "utilite": "Sert à X", "lien": "https://example.com"},
        "defi": {"titre": "Défi", "enonce": "Faire X", "indices": ["i1"]},
    }
    a.update(over)
    return a


@pytest.fixture
def setup(cfg):
    data = cfg.dir_donnees
    data.mkdir(parents=True)
    verified = [make_item(url=u) for u in (URL_TECH, URL_IA, URL_CC)]
    (data / "retenus.json").write_text(json.dumps(verified), encoding="utf-8")

    def go(a):
        (data / "analyse.json").write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
        return build_report(cfg, data / "analyse.json", data / "retenus.json",
                            History(data / "seen.json"), now=NOW)
    return go


def test_date_fr():
    assert date_fr("2026-11-06", with_weekday=True) == "vendredi 6 novembre 2026"


def test_rapport_complet(cfg, setup):
    out = setup(analysis())
    assert out.name == "rapport-2026-11-06.md"
    txt = out.read_text(encoding="utf-8")
    for titre in ("A. Résumé exécutif", "B. Actualité Tech", "C. Actualité IA",
                  "D. Focus Claude Code", "E. Ce que je dois retenir",
                  "F. Outil à découvrir", "G. Le défi technique du jour"):
        assert titre in txt
    assert URL_TECH in txt and "5 novembre 2026" in txt
    assert "rapport-2026-11-06.md" in (cfg.dir_rapports / "INDEX.md").read_text(encoding="utf-8")
    assert len(History(cfg.dir_donnees / "seen.json")) == 3


def test_url_non_verifiee_refusee(setup):
    a = analysis()
    a["tech"][0]["url"] = "https://inventé.example/fake"
    with pytest.raises(ReportError, match="absente des actus vérifiées"):
        setup(a)


def test_doublon_dans_rapport_refuse(setup):
    a = analysis()
    a["ia"][0]["url"] = URL_TECH
    with pytest.raises(ReportError, match="double"):
        setup(a)


def test_champs_obligatoires(setup):
    a = analysis()
    del a["tech"][0]["importance_dev"]
    a["outil"]["lien"] = ""
    with pytest.raises(ReportError) as e:
        setup(a)
    assert "importance_dev" in str(e.value) and "Outil" in str(e.value)


def test_journee_calme_acceptee(setup):
    a = analysis(tech=[], ia=[], note="Journée calme.")
    txt = setup(a).read_text(encoding="utf-8")
    assert "Aucune actualité tech vérifiée" in txt and "Journée calme." in txt


def test_version_email(cfg, setup):
    from veille.report import build_email
    html = build_email(cfg, setup(analysis())).read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>") and "<h2>A. Résumé exécutif</h2>" in html
    assert f'href="{URL_TECH}"' in html


def test_trop_d_actus_refuse(cfg, setup):
    a = analysis()
    a["tech"] = a["tech"] * 11
    with pytest.raises(ReportError, match="maximum"):
        setup(a)
