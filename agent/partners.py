"""Partner scouting for starred countries.

For every country in config.json -> starred_countries, Claude searches the web (company websites and public
LinkedIn company pages that appear in search results - no LinkedIn login or scraping) for companies active in
the same fields, then drafts a personalised collaboration email per company. Drafts go to the parsaint.group
webmail Drafts folder with the recipient address filled in only when the company publishes a generic business
address on its own website. Nothing is sent.
"""
import json
from datetime import datetime
from urllib.parse import urlparse

from . import mailbox
from .config import DATA_DIR, env

STATE_FILE = DATA_DIR / "partners.json"
STATUSES = {"drafted": "پیش‌نویس آماده", "sent": "ارسال شد", "replied": "پاسخ داد", "meeting": "جلسه",
            "mou": "تفاهم‌نامه", "not_interested": "علاقه‌مند نیست"}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["companies"],
    "properties": {"companies": {"type": "array", "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "city", "website", "linkedin_url", "email", "email_source", "sector_fa", "fit_fa",
                     "matched_products", "subject", "body"],
        "properties": {
            "name": {"type": "string"},
            "city": {"type": "string"},
            "website": {"type": "string"},
            "linkedin_url": {"type": "string", "description": "public LinkedIn company page if found in search, else empty"},
            "email": {"type": "string", "description": "generic business address published on the company's own site, else empty"},
            "email_source": {"type": "string", "description": "URL of the page where the address is published"},
            "sector_fa": {"type": "string", "description": "خصوصی / دولتی / شرکت دولتی and the field of activity, in Persian"},
            "fit_fa": {"type": "string"},
            "matched_products": {"type": "array", "items": {"type": "string"}},
            "subject": {"type": "string"},
            "body": {"type": "string", "description": "plain-text email, salutation to signature"},
        },
    }}},
}


def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"companies": {}, "scouted": {}}


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _key(website, name):
    host = urlparse(website if "//" in website else "https://" + website).netloc.lower().removeprefix("www.")
    return host or name.lower().strip()


def due_countries(cfg, state):
    pcfg = cfg.get("partner_scouting", {})
    out = []
    for country in cfg.get("starred_countries", []):
        last = state["scouted"].get(country)
        if not last or (datetime.now() - datetime.fromisoformat(last)).days >= pcfg.get("interval_days", 7):
            out.append(country)
    return out[:pcfg.get("max_countries_per_run", 2)]


def scout(cfg, analyst, state, open_tenders, use_mail, log):
    """Returns the list of company keys drafted in this run."""
    pcfg, c = cfg.get("partner_scouting", {}), cfg["company"]
    drafted = []
    for country in due_countries(cfg, state):
        known = [v["name"] for v in state["companies"].values() if v["country"] == country]
        tenders = [f"- {t['title']} ({t['url']})" for t in open_tenders if country.lower() in (t.get("country") or "").lower()]
        research = analyst._research(
            f"Find {pcfg.get('companies_per_country', 6)} established companies in {country} that work in the same "
            "fields as Parsa International Group (AI and digital solutions for energy/oil & gas, healthcare, aviation, "
            "nuclear power and smart cities): system integrators, engineering and IT firms, digital-transformation "
            "consultancies and industrial or medical software distributors that could act as local partner, lead "
            "bidder or reseller. Use the companies' own websites and public LinkedIn company pages that appear in "
            "search results; do not try to log in to LinkedIn. For each company give: name, city, website, LinkedIn "
            "company page, whether it is private or state-owned, what it does, and a generic business email "
            "address (info@, contact@, sales@, partnerships@ ...) only if it is published on the company's own "
            "website, with the URL of that page. Never give personal addresses of individuals and never guess an "
            f"address. Skip these already-contacted companies: {', '.join(known) or 'none'}.")
        if not research:
            log(f"Partner scouting {country}: no research result")
            continue
        result = analyst._structured(
            f"Country: {country}\nOpen tenders we track there:\n" + ("\n".join(tenders) or "(none)") +
            f"\n\nRESEARCH\n{research}\n\nFor each company write a short, specific collaboration email from "
            f"{c['signatory']} ({c['signatory_title']}, {c['name']}, {c['city']}): who we are, which of our product "
            "lines fit the company's business and why, an honest note that the products are advanced prototypes "
            "seeking pilot and validation partners, the proposed collaboration (local partner / lead bidder for "
            "public tenders, reseller or co-development; mention a matching open tender if there is one), and a "
            f"request for a short online call. Sign with name, title, company, {c['email']}, {c['website']}. "
            "Give each email its own subject line. Keep email empty when the research found no published address.",
            SCHEMA, cfg["llm"]["drafting_effort"])
        for co in result["companies"]:
            key = _key(co["website"], co["name"])
            if key in state["companies"]:
                continue
            record = {**co, "country": country, "status": "drafted", "found": datetime.now().date().isoformat()}
            msg = mailbox.build_message(env("IMAP_USER") or c["email"], co["subject"], co["body"], to=co["email"])
            if use_mail and mailbox.configured():
                try:
                    record["draft_saved_to"] = "webmail:" + mailbox.save_draft(msg, cfg)
                except Exception as exc:
                    log(f"  webmail draft failed for {co['name']}: {exc}")
                    record["draft_saved_to"] = "not saved"
            else:
                record["draft_saved_to"] = "not saved (webmail not configured)"
            state["companies"][key] = record
            drafted.append(key)
        state["scouted"][country] = datetime.now().isoformat(timespec="seconds")
        log(f"Partner scouting {country}: {len(result['companies'])} companies")
    return drafted
