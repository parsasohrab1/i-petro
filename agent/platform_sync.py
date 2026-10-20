"""Bridge between the market agent (files in data/) and the online platform (artifact database).

`export` writes one JSON file per database document under data/platform_export/<collection>/<doc_id>.json
plus a manifest of batches (max 50 writes each) that Claude applies with the ArtifactData tool.
`import_tracking` takes the tracking documents read back from the platform and merges them into
data/tenders.json so the daily Telegram reminders use the team's edits.
"""
import json
import re
import shutil

from . import events, investors, leads, partners, store
from .config import DATA_DIR, ROOT

EXPORT_DIR = DATA_DIR / "platform_export"
SAFE = re.compile(r"[^A-Za-z0-9_\-.~:@+]")

TENDER_KEEP = ("title", "country", "buyer", "source", "market", "line", "sector", "deadline", "deadline_fa", "days_left",
               "url", "status", "keyword_score", "domains", "facts", "setad_number")
ANALYSIS_KEEP = ("relevance_score", "summary_fa", "conditions", "eligibility", "eligibility_reasoning_fa",
                 "compliance_flags_fa", "next_actions_fa", "key_requirements_fa")


def _id(raw):
    return SAFE.sub("_", str(raw))[:200]


def _write(collection, doc_id, data, docs):
    path = EXPORT_DIR / collection / f"{_id(doc_id)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    docs.append({"collection": collection, "doc_id": _id(doc_id), "file_path": str(path)})


def export(include_seed=False):
    if EXPORT_DIR.exists():
        shutil.rmtree(EXPORT_DIR)
    docs = []
    state = store.load()
    for t in state["tenders"].values():
        if t["status"] not in store.ACTIVE:
            continue
        rec = {k: t.get(k) for k in TENDER_KEEP}
        rec["analysis"] = {k: (t.get("analysis") or {}).get(k) for k in ANALYSIS_KEEP} if t.get("analysis") else None
        _write("market/data/tenders", t["id"], rec, docs)
    for e in events.load()["events"].values():
        if events.is_upcoming(e):
            _write("market/data/events", e["id"], e, docs)
    for v in investors.load()["investors"].values():
        _write("market/data/investors", v["id"], {k: v.get(k) for k in v if k != "draft"}, docs)
    for lead in leads.load()["leads"].values():
        if lead.get("status") != "do_not_call":
            _write("market/data/leads", lead["id"], lead, docs)
    for key, p in partners.load()["companies"].items():
        _write("market/data/partners", key, p, docs)
    ops_file = DATA_DIR / "patent_ops.json"
    if ops_file.exists():
        for op in json.loads(ops_file.read_text(encoding="utf-8")).get("items", []):
            _write("patentops/data/items", op["id"], op, docs)
    if include_seed:
        seed = json.loads((ROOT / "platform" / "products_seed.json").read_text(encoding="utf-8"))
        for p in seed["products"]:
            rec = {k: v for k, v in p.items() if k not in ("id", "repo")}
            rec["github"] = seed["gh"] + p["repo"] if p.get("repo") else ""
            rec["similar"] = seed["similar"].get(p["id"], [])
            rec["patentability"] = ""
            _write("products", p["id"], rec, docs)
        for pat in seed["patents_from_repos"]:
            _write("patents", pat["id"], {k: v for k, v in pat.items() if k != "id"}, docs)
    batches = [docs[i:i + 50] for i in range(0, len(docs), 50)]
    (EXPORT_DIR / "manifest.json").write_text(json.dumps({"batches": batches}, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(docs), len(batches)


def import_tracking(folder):
    """Merge tracking docs saved by ArtifactData (out_dir) into data/tenders.json."""
    state = store.load()
    n = 0
    for f in sorted((folder).glob("**/tracking/*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        body = doc.get("data", doc)
        rec = state["tenders"].get(f.stem)
        if not rec:
            continue
        tr = rec.setdefault("tracking", {"log": []})
        for k in ("owner", "stage", "next_action", "next_date"):
            if body.get(k) is not None:
                tr[k] = body[k]
        tr["log"] = body.get("log", tr.get("log", []))
        n += 1
    store.save(state)
    return n
