"""Persistent pipeline state in data/tenders.json (plain JSON so it diffs cleanly in git).

Each tender moves through statuses until the RFP is closed:
new -> analysed -> partner_search | bid_prep -> mou_negotiation -> proposal_drafting -> submitted -> won | lost
plus: skipped, expired.
"""
import json
from datetime import datetime

from .config import DATA_DIR

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
                  "keyword_score", "domains", "facts", "market"):
            if tender.get(k) not in (None, ""):
                existing[k] = tender[k]
        return existing, False
    record = {**{k: v for k, v in tender.items() if k != "full_text"}, "status": "new", "first_seen": now(), "history": [{"at": now(), "status": "new"}]}
    state["tenders"][tender["id"]] = record
    return record, True


def set_status(record, status, note=""):
    if status not in STATUSES:
        raise ValueError(f"unknown status {status}; use one of {', '.join(STATUSES)}")
    record["status"] = status
    record.setdefault("history", []).append({"at": now(), "status": status, "note": note})
