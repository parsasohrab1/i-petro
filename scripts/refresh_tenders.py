#!/usr/bin/env python3
"""Refresh data/tenders.json from the recorded source sites.

Live collection runs for the sources reachable from this sandbox (TED EU notices,
World Bank procurement); Horizon Europe grant calls come back in from
grants_seed.json (store.seed_grants). Every collected tender is annotated with the
repo's own keyword map (screening.keyword_score / domains / days_left) so the
platform's Iran AI Projects / Overseas tabs place them in the right category.
Tenders whose deadline has passed are marked expired.

Hand-researched domestic notices (setadiran / sate, collected via web search when
the sites are not reachable) can be passed as a JSON file of tender dicts.

usage: python scripts/refresh_tenders.py [hand_collected.json]
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import screening, sources, store          # noqa: E402
from agent.config import load_config                 # noqa: E402
from agent import platform_sync                      # noqa: E402


def log(msg):
    print(f"[refresh] {msg}")


def refresh(hand_path=None):
    cfg = load_config()
    state = store.load()
    n_before = len(state["tenders"])

    seeded = store.seed_grants(state)
    if seeded:
        log(f"{seeded} grant calls re-added from grants_seed.json")

    raw = []
    for name, fn in (("TED (EU)", sources.fetch_ted), ("World Bank", sources.fetch_worldbank)):
        try:
            rows = fn(cfg, log)
            raw.extend(rows)
            log(f"{name}: {len(rows)} raw notices")
        except Exception as exc:   # keep going: one blocked site must not abort the run
            log(f"{name}: collection failed ({exc})")

    candidates = screening.screen(raw, cfg)
    log(f"{len(candidates)} collected notices passed keyword screening")
    new_ids = []
    for t in candidates:
        rec, is_new = store.upsert(state, t)
        if is_new:
            new_ids.append(rec["id"])
    log(f"{len(new_ids)} new tenders stored ({len(candidates) - len(new_ids)} refreshed in place)")

    hand, hand_ids = [], []
    if hand_path:
        hand = json.loads(Path(hand_path).read_text(encoding="utf-8"))
        for t in hand:
            t.setdefault("status", "new")
            t.setdefault("keyword_score", 3)
            t.setdefault("line", "ai")
            if not t.get("days_left") and t.get("deadline"):
                t["days_left"] = screening.days_left(t)
            rec, is_new = store.upsert(state, t)
            if is_new:
                hand_ids.append(rec["id"])
        log(f"hand-collected domestic: {len(hand)} processed, {len(hand_ids)} new")

    # pipeline refresh: days_left + expiry over the whole store
    expired = 0
    for rec in state["tenders"].values():
        rec["days_left"] = screening.days_left(rec)
        if rec["status"] in store.ACTIVE and rec["days_left"] is not None and rec["days_left"] < 0:
            store.set_status(rec, "expired")
            expired += 1
    store.save(state)
    log(f"expired: {expired}")

    # run log entry (same schema as pipeline.py writes) so monitoring history stays honest
    state.setdefault("runs", []).append({
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "collected": len(raw) + len(hand),
        "matched": len(candidates) + len(hand),
        "partner_drafts": [], "events_added": 0, "scholarships_added": 0,
        "investors_added": 0, "investor_drafts": [], "leads_added": 0, "papers_lines": [],
        "events_soon": [], "new_ids": new_ids + hand_ids, "actioned_ids": [], "reminders": [],
        "note": "sandbox refresh: TED + World Bank live; setadiran/sate not reachable from the sandbox, "
                "domestic added by hand after web research (see data/tenders_hand/)",
    })
    store.save(state)

    # summary
    tenders = state["tenders"].values()
    active = [t for t in tenders if t["status"] in store.ACTIVE]
    dom = [t for t in active if t.get("market") == "domestic"]
    intl = [t for t in active if t.get("market") != "domestic"]
    cats = {}
    for t in active:
        for d in t.get("domains", []) or ["other"]:
            cats[d] = cats.get(d, 0) + 1
    log(f"store: {n_before} -> {len(state['tenders'])} records | active {len(active)} "
        f"(domestic {len(dom)}, international {len(intl)})")
    log("active categories: " + json.dumps(cats, ensure_ascii=False))
    log(f"total tenders with domains: {sum(1 for t in tenders if t.get('domains'))}/{len(state['tenders'])}")

    n_docs, n_batches = platform_sync.export()
    log(f"platform export refreshed under {platform_sync.EXPORT_DIR} ({n_docs} docs, {n_batches} batches)")


if __name__ == "__main__":
    refresh(sys.argv[1] if len(sys.argv) > 1 else None)
