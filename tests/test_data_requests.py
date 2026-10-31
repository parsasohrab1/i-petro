import json

from agent import data_requests as dr


def reg():
    return {"assignee": "u_x", "assignee_name": "x", "created_by": "u_o", "due": "2026-11-07", "place_rule_fa": "rule",
            "datasets": [{"id": "a", "article": "s_a", "product": "p", "repo": "r", "module": "mod", "name": "Data A (big)", "license": "CC0", "url": "https://u", "files": ["f.csv"], "status": "blocked"},
                         {"id": "b", "article": "s_b", "product": "q", "repo": "r2", "module": "src", "name": "Data B", "license": "CC0", "url": "https://v", "files": ["g"], "status": "received"}]}


def test_task_doc_has_link_destination_and_assignee():
    r = reg(); t = dr.task_doc(r, r["datasets"][0], now="2026-10-31T00:00:00.000Z")
    assert t["kind"] == "data_download" and t["assignee"] == "u_x" and t["venue"] == "s_a" and t["status"] == "todo"
    assert "https://u" in t["desc"] and "research/mod/data_raw/" in t["desc"] and "data-upload" in t["desc"] and "rule" in t["desc"]
    assert t["title"] == "دانلود داده‌ها – Data A"


def test_export_only_blocked_and_create_only_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(dr, "EXPORT_DIR", tmp_path)
    w = dr.export(reg())
    assert [x["doc_id"] for x in w] == ["dr_a"] and all("if_version" not in x for x in w)
    assert json.loads((tmp_path / "dr_a.json").read_text(encoding="utf-8"))["dataset"] == "a"


def test_refresh_marks_received_when_files_present(tmp_path):
    r = reg(); (tmp_path / "r" / "research" / "mod" / "data_raw").mkdir(parents=True)
    assert dr.refresh(r, [tmp_path])[1] == []
    (tmp_path / "r" / "research" / "mod" / "data_raw" / "f.csv").write_text("x")
    r2, got = dr.refresh(r, [tmp_path]); assert got == ["a"] and r2["datasets"][0]["status"] == "received"
