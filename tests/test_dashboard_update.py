"""Tests for the prompt-driven dashboard updater (scripts/dashboard_update.py)."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("dashboard_update", ROOT / "scripts" / "dashboard_update.py")
du = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(du)


def _write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_upsert_section_dict_shaped(tmp_path):
    f = tmp_path / "events.json"
    _write(f, {"_note": "n", "events": {"ev-1": {"id": "ev-1", "name": "Old", "start": "2027-01-01"}}})
    added, updated = du.upsert_section(f, "events", [
        {"id": "ev-1", "name": "New name"},          # field merge into the existing record
        {"id": "ev-2", "name": "Second"},            # new record
    ])
    assert (added, updated) == (1, 1)
    state = json.loads(f.read_text(encoding="utf-8"))
    assert state["_note"] == "n"                                          # untouched
    assert state["events"]["ev-1"]["name"] == "New name"
    assert state["events"]["ev-1"]["start"] == "2027-01-01"               # existing fields kept
    assert state["events"]["ev-2"]["name"] == "Second"


def test_upsert_section_list_shaped(tmp_path):
    f = tmp_path / "patent_ops.json"
    _write(f, {"items": [{"id": "op-1", "title": "One"}]})
    added, updated = du.upsert_section(f, "items", [{"id": "op-1", "title": "One v2"}, {"id": "op-2", "title": "Two"}])
    assert (added, updated) == (1, 1)
    state = json.loads(f.read_text(encoding="utf-8"))
    assert {r["id"]: r["title"] for r in state["items"]} == {"op-1": "One v2", "op-2": "Two"}


def test_upsert_section_requires_id(tmp_path):
    f = tmp_path / "leads.json"
    import pytest
    with pytest.raises(SystemExit):
        du.upsert_section(f, "leads", [{"name": "no id"}])


def test_apply_articles(tmp_path, monkeypatch):
    reg = tmp_path / "article_registry.json"
    monkeypatch.setattr(du, "REGISTRY", reg)
    added, updated, total = du.apply_articles([
        {"id": "s_iqim", "venue": "IQIM 2027", "status_key": "ms"},
        {"id": "s_new", "venue": "New Venue 2028", "status_key": "abs", "product_key": "hqca"},
    ])
    assert (added, updated, total) == (2, 0, 2)   # empty tmp registry: both rows are new
    data = json.loads(reg.read_text(encoding="utf-8"))
    assert data["count"] == 2 and data["updated"] == str(__import__("datetime").date.today())
    by_id = {r["id"]: r for r in data["list"]}
    assert by_id["s_iqim"]["status_key"] == "ms"
    assert by_id["s_new"]["product_key"] == "hqca"
    # unknown fields are dropped, so a partial update cannot pollute the registry schema
    added, updated, total = du.apply_articles([{"id": "s_new", "status_key": "ms"}])
    assert (added, updated, total) == (0, 1, 2)
    assert json.loads(reg.read_text(encoding="utf-8"))["list"][1]["venue"] == "New Venue 2028"
