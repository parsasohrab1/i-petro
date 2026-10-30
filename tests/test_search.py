import json

from agent import search, store
from agent.config import load_config


def _tender(i, title):
    return {"id": i, "source": "TED (EU)", "market": "international", "title": title, "description": title, "buyer": "x",
            "country": "FRA", "deadline": "2099-01-01", "published": "2026-10-01", "url": "u", "facts": {}}


def test_adhoc_cfg_replaces_domains_and_days():
    cfg = load_config()
    c = search._adhoc_cfg(cfg, ["digital pathology"], 7)
    assert c["domains"] == {"adhoc": ["digital pathology"]}
    assert c["sources"]["ted"]["lookback_days"] == 7
    assert cfg["domains"].get("health_ai"), "health phrase list is configured"


def test_search_uses_only_chosen_sources(monkeypatch):
    calls = []
    monkeypatch.setattr(search, "fetch_ted", lambda c, log: calls.append("ted") or [_tender("TED-1", "t")])
    monkeypatch.setattr(search, "fetch_worldbank", lambda c, log: calls.append("wb") or [])
    assert len(search.search(load_config(), ["x"], ("ted",), 3, log=lambda m: None)) == 1
    assert calls == ["ted"]


def test_add_to_pipeline_screens_and_dedupes(monkeypatch, tmp_path):
    state = {"tenders": {}, "runs": []}
    monkeypatch.setattr(store, "load", lambda: state)
    monkeypatch.setattr(store, "save", lambda s: None)
    cfg = load_config()
    hits = [_tender("TED-1", "Digital health information system with artificial intelligence"), _tender("TED-2", "Office chairs")]
    ids = search.add_to_pipeline(cfg, hits, log=lambda m: None)
    assert ids == ["TED-1"] and set(state["tenders"]) == {"TED-1"}
    assert search.add_to_pipeline(cfg, hits, log=lambda m: None) == []
