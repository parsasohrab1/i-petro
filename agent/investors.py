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
DOMAINS = ["oil_gas", "aerospace", "nuclear", "water", "mining", "medical", "urban", "ai_cross_cutting"]

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


def _canon_all(state):
    from .taxonomy import canon_record
    for v in state.get("investors", {}).values():
        canon_record(v, "domains")
    return state


def load():
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["investors"]
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"investors": {}, "updated": ""}
    for inv in seed:
        state["investors"].setdefault(inv["id"], {**inv, "status": "new", "origin": "seed"})
    return _canon_all(state)


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
        "and accelerators worldwide that actively invest in AI applied to oil & gas, aerospace, nuclear, water, mining, "
        "healthcare and biotech and smart cities - with priority for "
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


# ------------------------------------------------------------ outreach drafts
DRAFTS_FILE = ROOT / "investor_drafts.json"

DRAFT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["subject", "body", "channel_fa"],
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string", "description": "plain-text email, salutation to signature"},
        "channel_fa": {"type": "string", "description": "best way to send it (application form, contact form, email), in Persian"},
    },
}


def _write_draft(cfg, rec, draft, use_mail, log):
    from . import mailbox
    from .config import OUTPUT_DIR, env
    sender = env("IMAP_USER") or cfg["company"]["email"]
    msg = mailbox.build_message(sender, draft["subject"], draft["body"], to=draft.get("to", ""))
    folder = OUTPUT_DIR / "investors"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{rec['id']}.eml").write_bytes(msg.as_bytes())
    rec["draft"] = {k: draft.get(k, "") for k in ("to", "subject", "body", "channel_fa")}
    if use_mail and mailbox.configured():
        try:
            rec["draft_saved_to"] = "webmail:" + mailbox.save_draft(msg, cfg)
            log(f"  investor draft saved to webmail: {rec['name']}")
        except Exception as exc:
            log(f"  investor draft for {rec['name']} not saved to webmail: {exc}")
            rec["draft_saved_to"] = "outputs/investors (webmail failed)"
    else:
        rec["draft_saved_to"] = "outputs/investors (webmail not configured)"


def outreach(cfg, analyst, state, profile_text, use_mail, log):
    """Draft an introduction email for every selected investor that has no webmail draft yet.
    Hand-written drafts in investor_drafts.json are used first; otherwise Claude writes one (when available)."""
    handwritten = json.loads(DRAFTS_FILE.read_text(encoding="utf-8"))["drafts"] if DRAFTS_FILE.exists() else {}
    c = cfg["company"]
    done = []
    for inv_id in cfg.get("selected_investors", []):
        rec = state["investors"].get(inv_id)
        if not rec or str(rec.get("draft_saved_to", "")).startswith("webmail"):
            continue
        draft = rec.get("draft") or handwritten.get(inv_id)
        if not draft and analyst is not None:
            draft = analyst._structured(
                f"INVESTOR\n{json.dumps({k: rec.get(k) for k in ('name', 'type', 'hq', 'stage_fa', 'ticket_fa', 'fund_fa', 'investments_fa', 'focus_fa', 'website', 'apply')}, ensure_ascii=False)}\n\n"
                f"Write a short introduction email from {c['signatory']} ({c['signatory_title']}, {c['name']}, {c['city']}) "
                "to this investor. Name the two or three product lines that match the investor's focus, be honest that the "
                "products are advanced prototypes (TRL 4-5) without commercial customers yet, say what we are seeking "
                "(pilot partners, seed funding or programme admission, matched to the investor's stage), acknowledge "
                "if our stage is earlier than the investor's usual stage, and ask for a short call. Sign with name, "
                f"title, company, city, {c['email']}, {c['website']}. Do not invent traction, customers or figures.",
                DRAFT_SCHEMA, cfg["llm"]["drafting_effort"])
            draft["to"] = rec.get("email", "")
        if not draft:
            continue
        if not draft.get("to") and rec.get("email"):
            draft["to"] = rec["email"]
        _write_draft(cfg, rec, draft, use_mail, log)
        done.append(inv_id)
    return done
