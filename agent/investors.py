"""Venture capital funds, corporate venture arms and accelerators relevant to the company's AI fields.

Starts from investors_seed.json (researched, with sources) and is refreshed weekly by Claude with web search:
new investors in the five fields, updated fund sizes and official application / contact pages.
"""
import json
import re
from datetime import date, datetime

from .config import DATA_DIR, ROOT

SEED_FILE = ROOT / "investors_seed.json"
STATE_FILE = DATA_DIR / "investors.json"

TYPES = {"vc": "صندوق خطرپذیر", "cvc": "سرمایه‌گذار شرکتی (CVC)", "accelerator": "شتاب‌دهنده"}
STATUSES = {"new": "جدید", "researching": "در حال بررسی", "contacted": "تماس گرفته شد", "meeting": "جلسه",
            "due_diligence": "بررسی دقیق (DD)", "term_sheet": "ترم‌شیت", "declined": "منتفی"}
DOMAINS = ["energy", "medical", "aviation", "nuclear", "urban", "ai_cross_cutting"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["investors"],
    "properties": {"investors": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "type", "hq", "domains", "stage_fa", "ticket_fa", "fund_fa", "investments_fa",
                     "focus_fa", "website", "apply", "email", "compliance_fa", "source"],
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": list(TYPES)},
            "hq": {"type": "string", "description": "country and city, in Persian"},
            "domains": {"type": "array", "items": {"type": "string", "enum": DOMAINS}},
            "stage_fa": {"type": "string"},
            "ticket_fa": {"type": "string", "description": "typical cheque / programme terms, or —"},
            "fund_fa": {"type": "string", "description": "fund size or AUM with year, or —"},
            "investments_fa": {"type": "string", "description": "number of investments and notable portfolio companies"},
            "focus_fa": {"type": "string"},
            "website": {"type": "string"},
            "apply": {"type": "string", "description": "official pitch / application page, or empty"},
            "email": {"type": "string", "description": "contact address published by the investor itself, or empty"},
            "compliance_fa": {"type": "string", "description": "e.g. US investor -> OFAC screening; empty if none"},
            "source": {"type": "string", "description": "page supporting the figures"},
        },
    }}},
}


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:50]


def load():
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["investors"]
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"investors": {}, "updated": ""}
    for inv in seed:
        state["investors"].setdefault(inv["id"], {**inv, "status": "new", "origin": "seed"})
    return state


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def due(state, cfg):
    last = state.get("updated")
    if not last:
        return True
    return (datetime.now() - datetime.fromisoformat(last)).days >= cfg.get("investors", {}).get("update_every_days", 7)


def update(cfg, analyst, state, log):
    known = ", ".join(sorted(v["name"] for v in state["investors"].values()))
    research = analyst._research(
        f"Today is {date.today().isoformat()}. Search the web for venture capital funds, corporate venture arms "
        "and accelerators worldwide that actively invest in AI applied to energy (oil & gas, power, grids), "
        "healthcare and biotech, aviation and aerospace, nuclear energy and smart cities - with priority for "
        "investors open to founders from Türkiye, the Gulf and Europe and for fields that are under-covered in "
        f"this list. Already listed (only report them if fund size or programme terms changed): {known}. For each "
        "investor give fund size or AUM with year, number of investments and notable portfolio companies, stage "
        "and cheque size, focus areas, official website, official pitch/application page, a contact email only "
        "if the investor publishes it itself, and a page that supports the figures. Note sanctions/compliance "
        "screening needs (e.g. US investors and OFAC).")
    if not research:
        log("Investors update: no research result")
        return 0
    found = analyst._structured("Convert this research into the investor list.\n\n" + research, SCHEMA, "medium")["investors"]
    by_name = {v["name"].lower(): k for k, v in state["investors"].items()}
    added = 0
    for inv in found:
        key = by_name.get(inv["name"].lower()) or _slug(inv["name"])
        if key in state["investors"]:
            old = state["investors"][key]
            old.update({k: inv[k] for k in ("fund_fa", "investments_fa", "ticket_fa", "apply", "source") if inv[k]})
        else:
            state["investors"][key] = {**inv, "id": key, "status": "new", "origin": "agent", "found": date.today().isoformat()}
            added += 1
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    log(f"Investors update: {added} new investors")
    return added
