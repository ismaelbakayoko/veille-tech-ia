import pytest

from veille.config import load_config
from veille.errors import ConfigError

from conftest import NOW


def test_config_charge(cfg):
    assert cfg.tz.key == "Africa/Abidjan"
    assert cfg.fenetre_heures == 24
    assert cfg.category("claude").section == "claude"
    assert "anthropic.com" in cfg.sources_niveau_1


def test_fenetre_24h(cfg):
    start, end = cfg.window(NOW)
    assert (end - start).total_seconds() == 24 * 3600
    assert end == NOW


def test_section_invalide(project):
    p = project / "config" / "categories.yaml"
    p.write_text("categories:\n  - {id: x, titre: X, section: autre}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="section"):
        load_config(project)


def test_categorie_en_double(project):
    p = project / "config" / "categories.yaml"
    p.write_text("categories:\n  - {id: x, titre: X, section: tech}\n"
                 "  - {id: x, titre: Y, section: ia}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="double"):
        load_config(project)


def test_ajout_categorie_sans_code(project):
    p = project / "config" / "categories.yaml"
    p.write_text(p.read_text(encoding="utf-8") +
                 "  - {id: quantique, titre: Informatique quantique, section: tech}\n",
                 encoding="utf-8")
    assert load_config(project).category("quantique").titre == "Informatique quantique"


def test_fuseau_inconnu(project):
    p = project / "config" / "settings.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("Africa/Abidjan", "Mars/Olympus"),
                 encoding="utf-8")
    with pytest.raises(ConfigError, match="Fuseau"):
        load_config(project)
