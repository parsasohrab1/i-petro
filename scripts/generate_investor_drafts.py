#!/usr/bin/env python3
"""Draft the introduction email for every investor with a matched product, as
info@parsaint.group, with the product pitch deck attached.

- Hand-written drafts in investor_drafts.json are preserved untouched (and get the
  deck attachment added when the investor has a matched product).
- For every other matched investor (requests_seed.json x data/investors.json), a
  personalised English draft is generated from the investor's focus, the matched
  product and the audited evidence. No invented traction.
- Every draft is written to outputs/investors/<id>.eml with the deck attached
  (open in Outlook -> save to Drafts), and the dashboard map is exported to
  data/platform_export/settings_investor_mail.json for `python -m agent export-platform`.

The agent never sends; drafts only. Final sending is always manual (user's Outlook).
"""
import json
import sys
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product_data import product_info, investor_matches  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DRAFTS_FILE = ROOT / "investor_drafts.json"
REQ_FILE = ROOT / "requests_seed.json"
INV_FILE = ROOT / "data" / "investors.json"
SEED_FILE = ROOT / "investors_seed.json"
DECK_DIR = ROOT / "outputs" / "pitch_decks"
EML_DIR = ROOT / "outputs" / "investors"
EXPORT_FILE = ROOT / "data" / "platform_export" / "settings_investor_mail.json"

SENDER = "info@parsaint.group"
SIGNER = "Narges Farahani"
TITLE = "AI Sector"
COMPANY = "Parsa International Group"
CITY = "Istanbul, Türkiye"
SITE = "parsaint.group"

import re
def slugfile(slug):
    return re.sub(r"[^A-Za-z0-9]+", "-", slug).strip("-")[:80] + ".pptx"


def ev_line(info):
    """One honest evidence sentence for the email body."""
    e = info["evidence"]
    if info["trl_label"].startswith("TRL 5 - validated"):
        return (f"Maturity: {info['trl_label']}. {e[1]['v']}.")
    if info["trl_label"].startswith("TRL 5 (catalogue"):
        return f"Maturity: TRL 5 (working platform / deployment claim in our catalogue)."
    return ("Maturity: validated prototype (TRL 4-5); the first real-data pilot on a partner site is the "
            "agreed next milestone, and we would value exactly this conversation with you.")


def focus_overlap(info, focus, rationale):
    """Two sentences tying investor focus to the matched product (uses the company's own match rationale)."""
    r = (rationale or "").strip().rstrip(".")
    if r:
        return f"Our match review points to {info['title'].split(' – ')[0]} as the strongest overlap with your focus: {r}."
    return f"Looking at your focus ({focus}), {info['title'].split(' – ')[0]} is the product in our portfolio with the closest overlap."


def draft_body(inv_name, info, rationale, focus, deck_name):
    prod_short = info["title"].split(" – ")[0]
    lines = [
        f"Dear {inv_name} Team,",
        "",
        f"My name is {SIGNER} from {COMPANY} ({CITY}). We build AI software for industrial operations "
        f"(oil, gas, petrochemical, energy) and healthcare, and I would like to introduce one specific product "
        f"rather than our whole portfolio, because it matches your focus most closely.",
        "",
        f"The product: {info['title']}",
        (info["desc"] or "").strip(),
        "",
        focus_overlap(info, focus, rationale),
        "",
        ev_line(info),
        "",
        f"A professional pitch deck is attached ({deck_name}) - it contains the technical summary, the validation "
        f"evidence with the exact datasets and measured results, and cited market data. If you prefer a walkthrough, "
        f"we are glad to give a short online presentation at your convenience.",
        "",
        "To be transparent about our stage: we are pre-commercial, seeking pilot partners and seed-stage funding, "
        "and we deliberately present each product to a single investor whose focus overlaps the most. "
        "Would you be open to a 20-minute online call in the coming weeks?",
        "",
        "Best regards,",
        "",
        SIGNER,
        TITLE,
        COMPANY,
        CITY,
        f"{SENDER}",
        SITE,
    ]
    return "\n".join(lines)


def build_eml(subject, body, attachment_path, to=""):
    msg = EmailMessage()
    msg["From"] = SENDER
    if to:
        msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    msg.set_content(body)
    if attachment_path and attachment_path.exists():
        data = attachment_path.read_bytes()
        msg.add_attachment(data, maintype="application",
                           subtype="vnd.openxmlformats-officedocument.presentationml.presentation",
                           filename=attachment_path.name)
    return msg


def main():
    inv_state = json.loads(INV_FILE.read_text(encoding="utf-8"))["investors"]
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["investors"]
    seed_by_id = {i["id"]: i for i in seed}
    reqs = json.loads(REQ_FILE.read_text(encoding="utf-8"))["requests"]
    existing = json.loads(DRAFTS_FILE.read_text(encoding="utf-8")) if DRAFTS_FILE.exists() else {"drafts": {}}
    drafts = dict(existing.get("drafts", {}))
    EML_DIR.mkdir(parents=True, exist_ok=True)

    mail_map = {}   # inv_id -> dashboard map entry
    generated = 0
    for r in reqs:
        iid = r.get("investor_id") or ""
        prod = r.get("product") or ""
        if not iid or prod in ("", "unmatched"):
            continue
        info = product_info(prod)
        deck_name = slugfile(prod)
        deck_path = DECK_DIR / deck_name
        inv = inv_state.get(iid) or seed_by_id.get(iid) or {}
        focus = inv.get("focus_fa") or (", ".join(inv.get("domains") or []))
        rationale = inv.get("match_rationale") or r.get("notes") or ""
        hand = drafts.get(iid)
        if hand:
            hand["attachment"] = deck_name
            if not hand.get("to") and inv.get("email"):
                hand["to"] = inv["email"]
            subject, body = hand["subject"], hand["body"]
        else:
            subject = f"{prod if prod in info['title'] else info['title'].split(' – ')[0]} - AI product matched to your focus | {COMPANY}"
            body = draft_body(inv.get("name") or r.get("investor") or iid, info, rationale, focus, deck_name)
            drafts[iid] = {
                "to": inv.get("email") or "",
                "channel_fa": f"از فرم تماس یا کانال رسمی سرمایه‌گذار ({r.get('channel') or 'وب‌سایت رسمی'})؛ درفت با پیچ دک ضمیمه آماده است",
                "subject": subject,
                "body": body,
                "attachment": deck_name,
                "product": prod,
            }
            generated += 1
        if deck_path.exists():
            msg = build_eml(subject, body, deck_path, drafts[iid].get("to") or "")
            (EML_DIR / f"{iid}.eml").write_bytes(msg.as_bytes())
        mail_map[iid] = {"to": drafts[iid].get("to") or "", "subject": subject, "body": body,
                          "attachment": deck_name if deck_path.exists() else "", "product": prod,
                          "investor": r.get("investor") or iid, "sender": SENDER}

    # hand-written drafts of investors without a request: attach the deck of their matched product if any
    for iid, d in drafts.items():
        if iid in mail_map:
            continue
        m = inv_state.get(iid) or {}
        prod = m.get("best_candidate_product") or ""
        if prod and prod not in ("unmatched", ""):
            deck_name = slugfile(prod)
            if (DECK_DIR / deck_name).exists():
                d.setdefault("attachment", deck_name)
                mail_map[iid] = {"to": d.get("to") or "", "subject": d["subject"], "body": d["body"],
                                  "attachment": deck_name, "product": prod, "investor": (seed_by_id.get(iid) or {}).get("name") or iid,
                                  "sender": SENDER}
            msg = build_eml(d["subject"], d["body"], DECK_DIR / d.get("attachment", ""), d.get("to") or "")
            (EML_DIR / f"{iid}.eml").write_bytes(msg.as_bytes())

    existing["drafts"] = drafts
    existing["_note_outlook"] = ("Drafts are saved as .eml (with the pitch deck attached) in outputs/investors/ and, when IMAP "
                                  "credentials are configured in .env, into the Drafts folder of info@parsaint.group webmail "
                                  "(python -m agent investor-outreach). Nothing is ever sent automatically.")
    DRAFTS_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_FILE.write_text(json.dumps({"path": "settings/investor_mail", "doc": {"map": mail_map}}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Drafts total: {len(drafts)} (generated now: {generated}) | .eml files: {len(list(EML_DIR.glob('*.eml')))} | dashboard map: {len(mail_map)}")


if __name__ == "__main__":
    main()
