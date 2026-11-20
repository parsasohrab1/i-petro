#!/usr/bin/env python3
"""Prompt-driven dashboard update (update method two).

The dashboard has two update paths:
  1. the artifact database (claude.ai), fed by data/platform_export (platform_sync.export);
  2. repo files picked up by the dashboard itself: data/tenders.json (market lists) and
     data/articles_export/article_registry.json (article registry tab).

This script applies a small JSON instruction file to both repo files so an agent session can
update the dashboard with a single commit — no artifact DB write required:

    {"tenders":  [ {...tender dict, needs id, market, title, ...} ],
     "articles": [ {"id": "...", "venue": "...", "title": "...", "product_key": "...",
                    "product_name": "...", "repo_url": "...", "status_key": "ms|abs",
                    "deadline": "...", "url": "..."} ]}

After running it, commit and push; the dashboard renders the changes from the repo files.
usage: python scripts/dashboard_update.py instruction.json
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import platform_sync, screening, store          # noqa: E402

REGISTRY = Path(__file__).resolve().parents[1] / "data" / "articles_export" / "article_registry.json"
ARTICLE_FIELDS = ("venue", "title", "product_key", "product_name", "repo_url", "status_key",
                  "deadline", "url", "kind", "abstract_words", "manuscript", "submitting_team_member")


def apply_tenders(state, items):
    added = 0
    for t in items:
        t.setdefault("status", "new")
        t.setdefault("keyword_score", 3)
        t.setdefault("line", "ai")
        t.setdefault("market", "domestic")
        if not t.get("days_left") and t.get("deadline"):
            t["days_left"] = screening.days_left(t)
        _, is_new = store.upsert(state, t)
        added += 1 if is_new else 0
    expired = 0
    for rec in state["tenders"].values():
        rec["days_left"] = screening.days_left(rec)
        if rec["status"] in store.ACTIVE and rec["days_left"] is not None and rec["days_left"] < 0:
            store.set_status(rec, "expired")
            expired += 1
    store.save(state)
    return added, expired


def apply_articles(items):
    reg = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {"updated": "", "count": 0, "list": []}
    reg.setdefault("list", [])
    added = updated = 0
    for a in items:
        if not a.get("id"):
            raise SystemExit("article record without 'id' — each registry row needs a stable id")
        row = {k: a[k] for k in ARTICLE_FIELDS if a.get(k) not in (None, "")}
        row["id"] = a["id"]
        existing = next((r for r in reg["list"] if r.get("id") == a["id"]), None)
        if existing:
            existing.update(row)
            updated += 1
        else:
            reg["list"].append(row)
            added += 1
    reg["count"] = len(reg["list"])
    reg["updated"] = str(date.today())
    REGISTRY.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return added, updated, len(reg["list"])


def main(path):
    ins = json.loads(Path(path).read_text(encoding="utf-8"))
    tenders = ins.get("tenders") or []
    articles = ins.get("articles") or []
    if not tenders and not articles:
        raise SystemExit("nothing to apply: the instruction file has no tenders/articles")

    log = []
    if tenders:
        state = store.load()
        added, expired = apply_tenders(state, tenders)
        log.append(f"tenders: {len(tenders)} processed ({added} new), {expired} expired; "
                   f"store now {len(state['tenders'])} records")
    if articles:
        added, updated, total = apply_articles(articles)
        log.append(f"articles: {len(articles)} processed ({added} new, {updated} updated); "
                   f"registry now {total} rows")

    n_docs, n_batches = platform_sync.export()
    log.append(f"platform export refreshed: {n_docs} docs in {n_batches} batches (method one stays in sync)")
    for line in log:
        print(f"[dashboard-update] {line}")
    print("[dashboard-update] now commit and push — the dashboard picks the changes up from the repo files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
