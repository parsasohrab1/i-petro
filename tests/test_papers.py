from datetime import date, timedelta

from agent import papers


class FakeAnalyst:
    def __init__(self, calls):
        self.calls = calls

    def _research(self, prompt):
        return "research text"

    def _structured(self, prompt, schema, effort):
        return {"calls": self.calls}


def call(name, product="ilift", days=60):
    d = (date.today() + timedelta(days=days)).isoformat()
    return dict(name=name, type="special", field="oil_gas", deadline=d, dl_note="", details="x", country="چین", city="پکن",
                url="https://e.org/cfp", source="https://e.org/cfp", impact="", present="none", product_id=product, fit_fa="مناسب")


def test_new_call_added_known_and_expired_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(papers, "STATE_FILE", tmp_path / "p.json")
    seed = papers.json.loads(papers.SEED_FILE.read_text(encoding="utf-8"))
    st = papers.load()
    expired = call("Old call", days=-5)
    new = call("Brand new special issue on lift AI")
    dup = call(seed[0]["name"])
    added = papers.update({"papers": {}}, FakeAnalyst([new, dup, expired]), st, lambda *_: None)
    assert [c["name"] for c in added] == [new["name"]]
    assert st["calls"][added[0]["id"]]["no_product"] is False


def test_call_without_product_is_flagged_and_notified(tmp_path, monkeypatch):
    monkeypatch.setattr(papers, "STATE_FILE", tmp_path / "p.json")
    st = papers.load()
    added = papers.update({"papers": {}}, FakeAnalyst([call("Fusion AI Symposium", product="none")]), st, lambda *_: None)
    assert added[0]["no_product"] is True
    text = "\n".join(papers.notification_lines(added))
    assert "محصول مناسب ندارند" in text and "Fusion AI Symposium" in text
    assert list(papers.export_doc(st)["map"].values())[0]["no_product"] is True


def test_same_call_not_added_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(papers, "STATE_FILE", tmp_path / "p.json")
    st = papers.load(); c = call("Once only")
    assert len(papers.update({"papers": {}}, FakeAnalyst([c]), st, lambda *_: None)) == 1
    assert papers.update({"papers": {}}, FakeAnalyst([c]), st, lambda *_: None) == []


def test_due_every_three_days():
    assert papers.due({"updated": ""}, {}) is True
    assert papers.due({"updated": papers.datetime.now().isoformat()}, {}) is False


def test_used_product_is_never_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(papers, "STATE_FILE", tmp_path / "p.json")
    st = papers.load(); cfg = {"papers": {"used_product_ids": ["ilift"]}}
    added = papers.update(cfg, FakeAnalyst([call("Lift conference", product="ilift")]), st, lambda *_: None)
    assert added[0]["no_product"] is True and added[0]["product_id"] == "none" and "قبلاً" in added[0]["fit_fa"]


def test_one_product_one_call_within_a_run(tmp_path, monkeypatch):
    monkeypatch.setattr(papers, "STATE_FILE", tmp_path / "p.json")
    st = papers.load()
    added = papers.update({"papers": {}}, FakeAnalyst([call("First iems call", product="iems"), call("Second iems call", product="iems")]), st, lambda *_: None)
    assert [c["no_product"] for c in added] == [False, True]
