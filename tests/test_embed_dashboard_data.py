"""Tests for the inline dashboard snapshot (scripts/embed_dashboard_data.py)."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("embed_dashboard_data", ROOT / "scripts" / "embed_dashboard_data.py")
emb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emb)


def test_build_covers_every_embedded_section():
    snap = emb.build()
    for key in ("tenders", "events", "investors", "leads", "partners", "requests", "schol",
                "calls", "products", "patents", "art_registry", "art_drafts"):
        assert key in snap, f"REPO_SNAPSHOT is missing '{key}'"
    assert len(snap["tenders"]) > 100                       # the Iran AI projects tab must have data
    t = next(iter(snap["tenders"].values()))
    for f in ("title", "market", "status", "days_left"):
        assert f in t
    assert len(t["description"]) <= 401                     # trim policy: 400 + ellipsis
    assert len(snap["art_registry"]["list"]) > 0


def test_payload_is_script_safe_and_parses_back():
    payload = json.dumps(emb.build(), ensure_ascii=False).replace("<", "\\u003c")
    assert "</script" not in payload                        # cannot break out of the script block
    round_trip = json.loads(payload.replace("\\u003c", "<"))
    assert round_trip["events"]


def test_inject_is_idempotent_and_before_the_app_script():
    html = "<html><head><title>x</title></head><body><script>APP();</script><script>more</script></body></html>"
    payload = "{}"
    once = emb.inject(html, payload)
    assert once.count(emb.BEGIN) == 1
    assert once.index("window.REPO_SNAPSHOT") < once.index("APP();")   # snapshot runs before the app
    twice = emb.inject(once, payload)
    assert twice.count(emb.BEGIN) == 1 and twice.count("window.REPO_SNAPSHOT") == 1
