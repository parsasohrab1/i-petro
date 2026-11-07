"""AI-related events in Iran and worldwide (conferences, exhibitions, summits).

The list starts from events_seed.json (researched and date-checked) and is refreshed daily by Claude with web
search. Each event carries a participation status that the user moves along (considering -> registered -> ...).
"""
import json
import re
from datetime import date, datetime

from .config import DATA_DIR, ROOT

SEED_FILE = ROOT / "events_seed.json"
STATE_FILE = DATA_DIR / "events.json"

STATUSES = {"new": "جدید", "considering": "در حال بررسی", "registered": "ثبت‌نام شد",
            "attending": "حضور قطعی", "attended": "شرکت کردیم", "skipped": "شرکت نمی‌کنیم"}

CATEGORIES = ["oil_gas", "aerospace", "nuclear", "water", "mining", "medical", "urban", "ai_cross_cutting"]

EVENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["events"],
    "properties": {"events": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "name_fa", "region", "country", "city", "start", "end", "date_fa", "date_status",
                     "usual_period_fa", "categories", "type", "why_fa", "participation_fa", "url", "source"],
        "properties": {
            "name": {"type": "string"},
            "name_fa": {"type": "string"},
            "region": {"type": "string", "enum": ["iran", "world"]},
            "country": {"type": "string", "description": "in Persian"},
            "city": {"type": "string", "description": "in Persian"},
            "start": {"type": "string", "description": "YYYY-MM-DD or empty when not announced"},
            "end": {"type": "string", "description": "YYYY-MM-DD or empty"},
            "date_fa": {"type": "string", "description": "for events in Iran: Persian (Jalali) date range WITH the year and the venue, e.g. '۲۹ آذر تا ۱ دی ۱۴۰۵ – تهران'; if not announced, state the last known edition with its year. Empty for events outside Iran."},
            "date_status": {"type": "string", "enum": ["confirmed", "to_verify", "tba"]},
            "usual_period_fa": {"type": "string", "description": "usual timing when dates are not announced, else empty"},
            "categories": {"type": "array", "items": {"type": "string", "enum": CATEGORIES}},
            "type": {"type": "string", "description": "Persian, e.g. نمایشگاه / کنفرانس / رویداد استارتاپی"},
            "why_fa": {"type": "string"},
            "participation_fa": {"type": "string", "description": "visitor / exhibitor / speaker / pitch, and deadlines"},
            "url": {"type": "string", "description": "official event website"},
            "source": {"type": "string", "description": "page that confirms the dates"},
        },
    }}},
}


def _slug(name, start):
    year = (start or "")[:4] or "tba"
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:50] + "-" + year


def _canon_all(state):
    from .taxonomy import canon_record
    for e in state.get("events", {}).values():
        canon_record(e, "categories")
    return state


def load():
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["events"]
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"events": {}, "updated": ""}
    events = state["events"]
    for e in seed:
        current = events.get(e["id"])
        if current is None:
            events[e["id"]] = {**e, "status": "new", "origin": "seed"}
        elif current.get("origin") == "seed":  # researched seed corrections win; the user's status is kept
            events[e["id"]] = {**current, **e, "status": current.get("status", "new"), "origin": "seed"}
    return _canon_all(state)


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def is_upcoming(e):
    end = e.get("end") or e.get("start")
    return not end or end >= date.today().isoformat()


def due(state, cfg):
    last = state.get("updated")
    if not last:
        return True
    return (datetime.now() - datetime.fromisoformat(last)).days >= cfg.get("events", {}).get("update_every_days", 1)


def update(cfg, analyst, state, log):
    """Daily refresh with web search: finds new events and corrects dates of known ones."""
    known = ", ".join(sorted({e["name"] for e in state["events"].values() if is_upcoming(e)}))
    horizon = cfg.get("events", {}).get("horizon_months", 12)
    research = analyst._research(
        f"Today is {date.today().isoformat()}. Search the web for upcoming AI-related events in the next {horizon} "
        "months that a young AI company from Istanbul/Iran should consider attending, exhibiting at or pitching at: "
        "AI conferences and summits, technology exhibitions with AI tracks, startup/investor events, and industry "
        "fairs where AI is applied to oil and gas, aerospace, nuclear power, water, mining, medicine/health or smart "
        "cities. Cover Iran (Tehran exhibitions, national AI events, technology-exchange events of public bodies; "
        "for every Iranian event give the Persian/Jalali date range with the year, or the last edition's date and year "
        "if the next one is not announced) "
        "and the world, prioritising Türkiye, the Gulf, Europe and Asia. Exclude military/defence events. "
        f"Already known (only report them if their dates changed): {known}. For every event give the official "
        "website and a page that confirms the dates; mark dates as unconfirmed when only one unofficial listing "
        "gives them.")
    if not research:
        log("Events update: no research result")
        return 0
    found = analyst._structured(
        f"Convert this research into the event list. Keep only events ending on or after {date.today().isoformat()}.\n\n"
        + research, EVENT_SCHEMA, "medium")["events"]
    added = 0
    by_name = {e["name"].lower(): k for k, e in state["events"].items()}
    for e in found:
        key = by_name.get(e["name"].lower()) or _slug(e["name"], e["start"])
        if key in state["events"]:
            old = state["events"][key]
            if e["start"] and e["date_status"] != "tba":
                old.update({k: e[k] for k in ("start", "end", "date_fa", "date_status", "url", "source") if e[k]})
        else:
            state["events"][key] = {**e, "id": key, "status": "new", "origin": "agent", "found": date.today().isoformat()}
            added += 1
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    log(f"Events update: {added} new events")
    return added


def set_status(state, event_id, status):
    if status not in STATUSES:
        raise ValueError(f"use one of {', '.join(STATUSES)}")
    state["events"][event_id]["status"] = status
