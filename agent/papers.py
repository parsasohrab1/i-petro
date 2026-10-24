"""Calls for papers (journal special issues, conferences) for the Articles tab of the platform.

Known venues come from papers_seed.json (the venues already in the platform). Every few days Claude searches the web for new
calls in the company's fields, matches each against the product list and flags the calls that no product fits, so that a new
product can be defined together. New calls are exported to the platform document settings/article_calls.
"""
import json
import re
from datetime import date, datetime

from .config import DATA_DIR, ROOT

SEED_FILE = ROOT / "papers_seed.json"
STATE_FILE = DATA_DIR / "papers.json"
FIELDS = ["oil_gas", "ai_industry", "medical", "quantum", "aerospace", "nuclear", "water", "energy"]

CALL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["calls"],
    "properties": {"calls": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "type", "field", "deadline", "dl_note", "details", "country", "city", "url", "source", "impact",
                     "present", "product_id", "fit_fa"],
        "properties": {
            "name": {"type": "string", "description": "venue and call title, e.g. 'Energy Geoscience – SI: AI for energy'"},
            "type": {"type": "string", "enum": ["journal", "special", "conf"]},
            "field": {"type": "string", "enum": FIELDS},
            "deadline": {"type": "string", "description": "submission/abstract deadline YYYY-MM-DD, empty when rolling or unknown"},
            "dl_note": {"type": "string", "description": "short note when the deadline is empty or ambiguous"},
            "details": {"type": "string", "description": "Persian, 1-2 sentences: topic, publisher, what to select when submitting"},
            "country": {"type": "string", "description": "in Persian"},
            "city": {"type": "string", "description": "in Persian; for journals the publisher's city"},
            "url": {"type": "string", "description": "official call page"},
            "source": {"type": "string", "description": "page that confirms the deadline (official site preferred)"},
            "impact": {"type": "string", "description": "impact factor as announced by the publisher, empty if unknown"},
            "present": {"type": "string", "enum": ["none", "inperson", "online", "hybrid", "unknown"]},
            "product_id": {"type": "string", "description": "id of the best-fitting product from the given list, or 'none' when no product fits"},
            "fit_fa": {"type": "string", "description": "Persian, one sentence: why this product fits, or what kind of new product would be needed"},
        },
    }}},
}


def load():
    return json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"calls": {}, "updated": ""}


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _norm(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _slug(name, deadline):
    return "c_" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:50] + "-" + ((deadline or "")[:4] or "open")


def is_open(c):
    return not c.get("deadline") or c["deadline"] >= date.today().isoformat()


def due(state, cfg):
    last = state.get("updated")
    if not last:
        return True
    return (datetime.now() - datetime.fromisoformat(last)).days >= cfg.get("papers", {}).get("update_every_days", 3)


def products_text(cfg):
    prods = json.loads((ROOT / "products.json").read_text(encoding="utf-8"))["products"]
    lines = [f"- {p['id']}: {p['name']} – {p['summary']}" for p in prods]
    return "\n".join(lines)


def no_product(c):
    return c.get("product_id") in ("", "none", None)


def update(cfg, analyst, state, log):
    """Search for new calls; returns the list of newly added calls (each carries `no_product`)."""
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8")) if SEED_FILE.exists() else []
    known = {_norm(s["name"]) for s in seed} | {_norm(c["name"]) for c in state["calls"].values()}
    known_text = "; ".join(sorted({s["name"][:60] for s in seed} | {c["name"][:60] for c in state["calls"].values()}))
    horizon = cfg.get("papers", {}).get("horizon_months", 9)
    research = analyst._research(
        f"Today is {date.today().isoformat()}. Search the web for NEW open calls for papers with a submission deadline in the "
        f"next {horizon} months (or rolling calls of special issues) that suit a company building AI products for: oil and "
        "gas, industrial AI / predictive maintenance / digital twins, medicine and health AI, quantum computing applications, "
        "aviation, nuclear power, water and energy. Include journal special issues and conferences/symposia (IEEE, Elsevier, "
        "Springer, MDPI, Frontiers, SPE, EAGE and similar). Prefer official call pages and give the deadline from the official "
        f"page. Skip predatory venues and anything military. Already known (do not repeat): {known_text}")
    if not research:
        log("Papers update: no research result")
        return []
    found = analyst._structured(
        f"Convert this research into calls. Keep only calls whose deadline is empty or on/after {date.today().isoformat()}. "
        "For each call pick product_id from this list, or 'none' when no product genuinely fits:\n" + products_text(cfg)
        + "\n\nResearch:\n" + research, CALL_SCHEMA, "medium")["calls"]
    added = []
    for c in found:
        if _norm(c["name"]) in known or not is_open(c):
            continue
        key = _slug(c["name"], c["deadline"])
        if key in state["calls"]:
            continue
        rec = {**c, "id": key, "found": date.today().isoformat(), "ver": bool(c.get("source") and c["source"] == c.get("url")),
               "no_product": no_product(c), "ack": False}
        state["calls"][key] = rec
        added.append(rec)
        known.add(_norm(c["name"]))
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    log(f"Papers update: {len(added)} new calls, {sum(1 for a in added if a['no_product'])} without a product")
    return added


def notification_lines(added):
    """Telegram/email lines: new calls, with those that no product fits listed first."""
    lines = []
    orphan = [c for c in added if c["no_product"]]
    if added:
        lines.append(f"\n📝 {len(added)} فراخوان جدید مقاله به تب مقالات افزوده شد")
    if orphan:
        lines.append("⚠️ این فراخوان‌ها محصول مناسب ندارند؛ برای تعریف محصول جدید با هم‌فکری اقدام کنیم:")
        for c in orphan[:10]:
            lines.append(f"• {c['name'][:80]} – ددلاین {c['deadline'] or 'نامشخص'} – {c['fit_fa'][:90]}")
    return lines


def export_doc(state):
    """The document settings/article_calls: {map: {id: venue}} for open calls only."""
    keep = ("id", "name", "type", "field", "deadline", "dl_note", "details", "country", "city", "url", "source", "impact",
            "present", "product_id", "fit_fa", "found", "ver", "no_product", "ack")
    return {"map": {k: {f: c.get(f) for f in keep} for k, c in state["calls"].items() if is_open(c)}}
