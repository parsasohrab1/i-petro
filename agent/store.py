"""Persistent pipeline state in data/tenders.json (plain JSON so it diffs cleanly in git).

Each tender moves through statuses until the RFP is closed:
new -> analysed -> partner_search | bid_prep -> mou_negotiation -> proposal_drafting -> submitted -> won | lost
plus: skipped, expired.
"""
import json
from datetime import datetime

from .config import DATA_DIR, ROOT

STATE_FILE = DATA_DIR / "tenders.json"

STATUSES = {
    "new": "جدید",
    "analysed": "تحلیل شده",
    "partner_search": "در جست‌وجوی شریک",
    "bid_prep": "آماده‌سازی پیشنهاد (مستقیم)",
    "mou_negotiation": "مذاکره تفاهم‌نامه",
    "proposal_drafting": "نگارش پروپوزال",
    "submitted": "ارسال شده",
    "won": "برنده",
    "lost": "بازنده",
    "skipped": "کنار گذاشته شد",
    "expired": "منقضی",
}
ACTIVE = {"new", "analysed", "partner_search", "bid_prep", "mou_negotiation", "proposal_drafting", "submitted"}


def now():
    return datetime.now().isoformat(timespec="seconds")


def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"tenders": {}, "runs": []}


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def upsert(state, tender):
    existing = state["tenders"].get(tender["id"])
    if existing:
        # refresh listing fields, keep pipeline fields
        for k in ("title", "description", "deadline", "deadline_fa", "url", "buyer", "country", "days_left",
                  "keyword_score", "domains", "facts", "market", "sector", "line"):
            if tender.get(k) not in (None, ""):
                existing[k] = tender[k]
        return existing, False
    record = {**{k: v for k, v in tender.items() if k != "full_text"}, "status": "new", "first_seen": now(), "history": [{"at": now(), "status": "new"}]}
    state["tenders"][tender["id"]] = record
    return record, True


def seed_grants(state):
    """Grant calls researched by hand (grants_seed.json) are re-added on every run if the cached state lacks them,
    because the daily job restores data/ from the Actions cache and would otherwise drop hand-edited records."""
    f = ROOT / "grants_seed.json"
    if not f.exists():
        return 0
    added = 0
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["id"] not in state["tenders"]:
            upsert(state, dict(r))
            added += 1
    return added


def set_status(record, status, note=""):
    if status not in STATUSES:
        raise ValueError(f"unknown status {status}; use one of {', '.join(STATUSES)}")
    record["status"] = status
    record.setdefault("history", []).append({"at": now(), "status": status, "note": note})


# ------------------------------------------------------------- follow-up tracking
STAGES = {
    "identified": "شناسایی",
    "documents": "دریافت مدارک",
    "partner_email": "ارسال ایمیل به شریک تجاری",
    "partner_meeting": "پاسخ / جلسه با شریک",
    "mou": "امضای تفاهم‌نامه",
    "proposal": "تهیه‌ی پروپوزال",
    "submitted": "ارسال پیشنهاد",
    "result": "اعلام نتیجه",
}


def track(record, owner=None, stage=None, next_action=None, next_date=None, note=""):
    """Update the follow-up fields of a tender and keep a history line."""
    if stage is not None and stage not in STAGES:
        raise ValueError(f"unknown stage {stage}; use one of {', '.join(STAGES)}")
    tr = record.setdefault("tracking", {"owner": "", "stage": "identified", "next_action": "", "next_date": "", "log": []})
    changes = []
    for key, value in (("owner", owner), ("stage", stage), ("next_action", next_action), ("next_date", next_date)):
        if value is not None and value != tr.get(key):
            tr[key] = value
            changes.append(f"{key}={STAGES.get(value, value) if key == 'stage' else value}")
    if changes or note:
        tr["log"].append({"at": now(), "change": "، ".join(changes), "note": note})
    tr["updated"] = now()
    return tr
