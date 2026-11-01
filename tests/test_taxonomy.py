from agent.taxonomy import canon_domains, canon_record, sector_of_text, SECTORS


def test_legacy_energy_is_split_by_text():
    assert canon_domains(["energy"], "Nuclear plant monitoring") == ["nuclear"]
    assert canon_domains(["energy"], "Copper mine optimisation") == ["mining"]
    assert canon_domains(["energy"], "Hydrology forecasting for dams") == ["water"]
    assert canon_domains(["energy"], "Refinery fuel optimisation") == ["oil_gas"]
    assert canon_domains(["energy"], "More storage core") == ["oil_gas"]   # "more"/"store"/"core" must not read as ore/mining


def test_aviation_renamed_and_duplicates_removed():
    assert canon_domains(["aviation", "aerospace", "medical"]) == ["aerospace", "medical"]
    assert canon_domains(["energy", "oil_gas"], "gas turbine") == ["oil_gas"]


def test_record_and_sector_list():
    r = canon_record({"domains": ["energy", "urban"], "title": "Solar grid tender"}, "domains")
    assert r["domains"] == ["oil_gas", "urban"]
    assert set(SECTORS) == {"oil_gas", "aerospace", "nuclear", "water", "mining"}
    assert sector_of_text("") == "oil_gas"


def test_config_uses_new_domain_keys():
    import json
    from agent.config import ROOT
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert "energy" not in cfg["domains"] and "aviation" not in cfg["domains"]
    assert set(SECTORS) <= set(cfg["domains"])
    assert set(SECTORS) <= set(cfg["domain_labels_fa"])
