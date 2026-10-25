"""Fully funded Master / PhD scholarships outside China and Russia.

The list starts from scholarships_seed.json (researched, with sources) and is refreshed daily by Claude with web
search. Two Word files are rebuilt after every refresh: the opportunity list by country and the owner's to-do list.
"""
import json
import re
from datetime import date, datetime

from .config import DATA_DIR, ROOT

SEED_FILE = ROOT / "scholarships_seed.json"
STATE_FILE = DATA_DIR / "scholarships.json"
EXCLUDED = ("چین", "روسیه", "china", "russia")   # excluded by request

STATUSES = {"new": "جدید", "considering": "در حال بررسی", "preparing": "در حال آماده‌سازی", "applied": "ارسال شد",
            "skipped": "نمی‌خواهم"}

SCHOLARSHIP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["scholarships"],
    "properties": {"scholarships": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "country", "region", "uni", "levels", "field", "support", "deadline", "deadline_note",
                     "url", "source", "ai_relevant"],
        "properties": {
            "name": {"type": "string"},
            "country": {"type": "string", "description": "in Persian"},
            "region": {"type": "string", "enum": ["uk", "europe", "other"]},
            "uni": {"type": "string"},
            "levels": {"type": "array", "items": {"type": "string", "enum": ["master", "phd"]}},
            "field": {"type": "string"},
            "support": {"type": "string", "description": "Persian: what is covered (tuition, stipend, travel...)"},
            "deadline": {"type": "string", "description": "YYYY-MM-DD or empty when rolling/unknown"},
            "deadline_note": {"type": "string", "description": "Persian"},
            "url": {"type": "string", "description": "official page"},
            "source": {"type": "string"},
            "ai_relevant": {"type": "boolean"},
        },
    }}},
}


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:50] or "sch"


def excluded(rec):
    text = f"{rec.get('country', '')} {rec.get('uni', '')}".lower()
    return any(x in text for x in EXCLUDED)


def load():
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["scholarships"]
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"scholarships": {}, "updated": ""}
    items = state["scholarships"]
    for s in seed:
        current = items.get(s["id"])
        if current is None:
            items[s["id"]] = {**s, "status": s.get("status0", "new")}
        elif current.get("origin") == "seed":  # researched seed corrections win; the user's status is kept
            items[s["id"]] = {**current, **s, "status": current.get("status", "new")}
    for k in [k for k, v in items.items() if excluded(v)]:
        del items[k]
    return state


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def days_left(rec):
    if not rec.get("deadline"):
        return None
    return (date.fromisoformat(rec["deadline"]) - date.today()).days


def is_closed(rec):
    d = days_left(rec)
    return d is not None and d < 0


def due(state, cfg):
    last = state.get("updated")
    if not last:
        return True
    return (datetime.now() - datetime.fromisoformat(last)).days >= cfg.get("scholarships", {}).get("update_every_days", 1)


def update(cfg, analyst, state, log):
    """Daily refresh with web search: finds new fully funded positions and corrects deadlines of known ones."""
    known = ", ".join(sorted(s["name"] for s in state["scholarships"].values() if not is_closed(s)))
    research = analyst._research(
        f"Today is {date.today().isoformat()}. Search the web for fully funded (tuition + stipend) Master's and PhD "
        "scholarships and funded PhD positions open to Iranian / international applicants, in AI, machine learning and "
        "AI applied to oil and gas, health, quantum computing, aviation and nuclear. Cover the whole world EXCEPT China "
        "and Russia, with priority on the United Kingdom (including the University of Derby) and Europe. Only report "
        "opportunities whose deadline is on or after today or that are rolling. "
        f"Already known (report them only if their deadline or funding changed): {known}. For every item give the "
        "official page and the page that confirms the deadline; leave the deadline empty if only unofficial listings "
        "give it and say so in the note.")
    if not research:
        log("Scholarships update: no research result")
        return 0
    found = analyst._structured(
        f"Convert this research into the scholarship list. Drop China and Russia and anything closed before "
        f"{date.today().isoformat()}.\n\n" + research, SCHOLARSHIP_SCHEMA, "medium")["scholarships"]
    added = 0
    by_name = {s["name"].lower(): k for k, s in state["scholarships"].items()}
    for s in found:
        if excluded(s):
            continue
        key = by_name.get(s["name"].lower()) or _slug(s["name"])
        if key in state["scholarships"]:
            old = state["scholarships"][key]
            old.update({k: s[k] for k in ("deadline", "deadline_note", "support", "url") if s[k]})
        else:
            state["scholarships"][key] = {**s, "id": key, "status": "new", "origin": "agent", "note": "",
                                          "found": date.today().isoformat()}
            added += 1
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    log(f"Scholarships update: {added} new")
    return added


def set_status(state, sid, status):
    if status not in STATUSES:
        raise ValueError(f"use one of {', '.join(STATUSES)}")
    state["scholarships"][sid]["status"] = status
