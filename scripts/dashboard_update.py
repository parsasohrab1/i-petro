#!/usr/bin/env python3
"""Prompt-driven dashboard update (update method two).

The dashboard has two update paths:
  1. the artifact database (claude.ai), fed by data/platform_export (platform_sync.export);
  2. repo files picked up by the dashboard itself (REPO_BASE in platform/index.html):
     data/tenders.json, data/events.json, data/investors.json, data/leads.json,
     data/partners.json, data/scholarships.json, data/patent_ops.json, data/papers.json,
     requests_seed.json, platform/products_seed.json and
     data/articles_export/article_registry.json (article registry tab).

This script applies a small JSON instruction file to those repo files so an agent session can
update the dashboard with a single commit — no artifact DB write required:

    {"tenders":  [ {...tender dict, needs id, market, title, ...} ],
     "articles": [ {"id": "...", "venue": "...", "title": "...", "product_key": "...",
                    "product_name": "...", "repo_url": "...", "status_key": "ms|abs",
                    "deadline": "...", "url": "..."} ],
     "events":   [ {"id": "...", "name": "...", "start": "...", "url": "..."} ],
     "investors":[ {"id": "...", "name": "...", "domains": [...], ...} ],
     "leads":    [ {"id": "...", "name": "...", "url": "..."} ],
     "scholarships": [ {"id": "...", "name": "...", "country": "..."} ],
     "requests": [ {"id": "...", "title": "...", ...} ],
     "patent_ops": [ {"id": "...", "title": "..."} ]}

Every record needs a stable "id". After running it, commit and push; the dashboard renders the
changes from the repo files.
usage: python scripts/dashboard_update.py instruction.json
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import platform_sync, screening, store          # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REGISTRY = DATA / "articles_export" / "article_registry.json"
ARTICLE_FIELDS = ("venue", "title", "product_key", "product_name", "repo_url", "status_key",
                  "deadline", "url", "kind", "abstract_words", "manuscript", "submitting_team_member")
# section name -> (state file, top-level key holding the records); tenders and articles have
# dedicated handlers, everything else goes through the generic upsert_section below
SECTIONS = {
    "events": (DATA / "events.json", "events"),
    "investors": (DATA / "investors.json", "investors"),
    "leads": (DATA / "leads.json", "leads"),
    "partners": (DATA / "partners.json", "companies"),
    "scholarships": (DATA / "scholarships.json", "scholarships"),
    "requests": (ROOT / "requests_seed.json", "requests"),
    "patent_ops": (DATA / "patent_ops.json", "items"),
}


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


def upsert_section(path, list_key, items):
    """Generic repo-file upsert used by every SECTIONS entry; records are merged by id.

    Works for both shapes the agent modules use: dict-of-records (events, investors, leads,
    scholarships) and list-of-records (requests, patent_ops items). The rest of the file is
    preserved untouched (_note, updated, runs, ...).
    """
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    rows = state.setdefault(list_key, [] if list_key in ("items", "requests") else {})
    if not isinstance(rows, (list, dict)):
        raise SystemExit(f"{path.name}: '{list_key}' is {type(rows).__name__}, expected list/dict")
    added = updated = 0
    for a in items:
        row = dict(a)
        if not row.get("id"):
            raise SystemExit(f"{path.name}: record without 'id' — every row needs a stable id")
        if isinstance(rows, list):
            existing = next((r for r in rows if r.get("id") == row["id"]), None)
            if existing:
                existing.update(row)
                updated += 1
            else:
                rows.append(row)
                added += 1
        else:
            existing = rows.get(row["id"])
            if existing:
                existing.update(row)
                updated += 1
            else:
                rows[row["id"]] = row
                added += 1
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return added, updated


def main(path):
    ins = json.loads(Path(path).read_text(encoding="utf-8"))
    tenders = ins.get("tenders") or []
    articles = ins.get("articles") or []
    generic = [(name, cfg) for name, cfg in SECTIONS.items() if ins.get(name)]
    if not tenders and not articles and not generic:
        raise SystemExit("nothing to apply: the instruction file has no tenders/articles/"
                         + "/".join(sorted(SECTIONS)))

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
    for name, (fpath, list_key) in generic:
        added, updated = upsert_section(fpath, list_key, ins[name])
        log.append(f"{name}: {len(ins[name])} processed ({added} new, {updated} updated) in {fpath.name}")

    n_docs, n_batches = platform_sync.export()
    log.append(f"platform export refreshed: {n_docs} docs in {n_batches} batches (method one stays in sync)")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "embed_dashboard_data.py")],
                       capture_output=True, text=True)
    if r.returncode == 0:
        log.append("inline REPO_SNAPSHOT rebuilt in platform/index.html — commit index.html too; "
                   "updating the artifact HTML alone then refreshes every section")
    else:
        log.append(f"WARNING: embed rebuild failed: {(r.stderr or '').strip()}")
    for line in log:
        print(f"[dashboard-update] {line}")
    print("[dashboard-update] now commit and push — the dashboard picks the changes up from the repo files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
