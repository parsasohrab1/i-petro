import json

from agent import store


def test_seed_grants_adds_missing_and_keeps_existing_status(tmp_path, monkeypatch):
    seed = tmp_path / "grants_seed.json"
    seed.write_text(json.dumps([{"id": "GRANT-X", "title": "t", "market": "international", "domains": ["medical"]},
                                {"id": "GRANT-Y", "title": "u", "market": "international", "domains": ["medical"]}]), encoding="utf-8")
    monkeypatch.setattr(store, "ROOT", tmp_path)
    state = {"tenders": {}, "runs": []}
    assert store.seed_grants(state) == 2
    store.set_status(state["tenders"]["GRANT-X"], "submitted")
    assert store.seed_grants(state) == 0                      # second run: nothing re-added, status untouched
    assert state["tenders"]["GRANT-X"]["status"] == "submitted"
    assert state["tenders"]["GRANT-Y"]["domains"] == ["medical"]


def test_real_seed_file_is_valid():
    from agent.config import ROOT
    rows = json.loads((ROOT / "grants_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 4 and all(r["id"].startswith("GRANT-") and "medical" in r["domains"] for r in rows)
