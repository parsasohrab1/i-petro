"""Daily run: collect -> screen -> analyse -> draft (partner email + MoU, or direct EOI) -> remind -> dashboard -> notify."""
import json
from datetime import date, timedelta

from . import contact_email, dashboard, documents, events, investors, leads, mailbox, memory, notify, papers, partners, scholarship_docs, scholarships, store
from .analyst import Analyst, llm_available
from .config import OUTPUT_DIR, env, load_config
from .portfolio import build_profile, profile_text
from .screening import days_left, screen
from .sources import collect_all, enrich_full_text

REMIND_AT = {14, 7, 3, 1}


def _log_factory(lines):
    def log(msg):
        print(msg, flush=True)
        lines.append(msg)
    return log


def _sender(cfg):
    return env("IMAP_USER") or cfg["company"]["email"]


def _save_json(tender, name, data):
    path = documents.tender_dir(tender["id"]) / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _draft(cfg, rec, subject, body, attachments, to, use_mail, log):
    """Store the email as .eml next to the tender files and, if configured, in the webmail Drafts folder."""
    msg = mailbox.build_message(_sender(cfg), subject, body, to=to, attachments=attachments)
    eml = documents.tender_dir(rec["id"]) / "draft.eml"
    eml.write_bytes(msg.as_bytes())
    rec.setdefault("files", {})["draft_eml"] = eml.relative_to(OUTPUT_DIR.parent).as_posix()
    if use_mail and mailbox.configured():
        try:
            folder = mailbox.save_draft(msg, cfg)
            rec["draft_saved_to"] = f"webmail:{folder}"
            log(f"  draft saved to webmail folder {folder}")
        except Exception as exc:
            log(f"  could not save webmail draft: {exc}")
            rec["draft_saved_to"] = "local .eml only"
    else:
        rec["draft_saved_to"] = "local .eml only"


def process_candidate(analyst, cfg, rec, use_mail, budget, log):
    log(f"Analysing {rec['id']}: {rec['title'][:90]}")
    analysis = analyst.analyse({**rec, "analysis_text": enrich_full_text(rec, log)})
    rec["analysis"] = analysis
    _save_json(rec, "analysis.json", analysis)
    if analysis["relevance_score"] < 40 or analysis["eligibility"] == "not_feasible":
        store.set_status(rec, "skipped", f"relevance {analysis['relevance_score']}, {analysis['eligibility']}")
        return None
    store.set_status(rec, "analysed")
    if analysis["eligibility"] == "partner_required":
        if budget["partner"] <= 0:
            return "analysed"
        budget["partner"] -= 1
        pkg = analyst.partner_package(rec, analysis)
        _save_json(rec, "partner_package.json", pkg)
        mou = documents.write_mou(rec, pkg, cfg["company"])
        rec.setdefault("files", {})["mou"] = mou.relative_to(OUTPUT_DIR.parent).as_posix()
        for p in pkg["partner_candidates"]:   # read the partner's own website for its published business address
            found, src = contact_email.find_email(p.get("website", ""), log)
            if found:
                p["public_contact"], p["contact_source"] = found, src
        rec["partners"] = pkg["partner_candidates"]
        first_contact = next((p["public_contact"] for p in pkg["partner_candidates"] if p["public_contact"]), "")
        _draft(cfg, rec, pkg["email_subject"], pkg["email_body"], [mou], first_contact, use_mail, log)
        rec["suggested_to"] = first_contact
        store.set_status(rec, "partner_search", "partner email + MoU drafted")
        store.track(rec, stage="partner_email", next_action="ارسال ایمیل همکاری از Drafts وب‌میل به شریک", note="پیش‌نویس ایمیل و MoU آماده شد")
        return "partner_search"
    pkg = analyst.direct_package(rec, analysis)
    _save_json(rec, "direct_package.json", pkg)
    checklist = documents.write_checklist(rec, pkg["checklist_fa"])
    rec.setdefault("files", {})["checklist"] = checklist.relative_to(OUTPUT_DIR.parent).as_posix()
    _draft(cfg, rec, pkg["letter_subject"], pkg["letter_body"], [], "", use_mail, log)
    store.set_status(rec, "bid_prep", "EOI letter + checklist drafted")
    store.track(rec, stage="documents", next_action="دریافت اسناد مناقصه و تکمیل چک‌لیست", note="نامه‌ی ابراز علاقه و چک‌لیست آماده شد")
    return "bid_prep"


def summary_text(cfg, run, state):
    t = state["tenders"]
    lines = [f"✅ {cfg['agent_name_fa']} – اسکن روزانه {date.today().isoformat()} انجام شد",
             f"منابع بررسی‌شده: {run['collected']} آگهی | مرتبط: {run['matched']} | جدید: {len(run['new_ids'])}"]
    ready = [t[i] for i in run["actioned_ids"]]
    if ready:
        lines.append("\n📌 کارهایی که در انتظار شماست:")
        for r in ready:
            a = r.get("analysis", {})
            kind = "پیش‌نویس ایمیل شریک + تفاهم‌نامه" if r["status"] == "partner_search" else "نامه ابراز علاقه + چک‌لیست"
            where = "در Drafts وب‌میل" if str(r.get("draft_saved_to", "")).startswith("webmail") else "در پوشه outputs"
            lines.append(f"• {r['country'] or '؟'} | {r['title'][:80]}\n  امتیاز {a.get('relevance_score', '-')} | "
                         f"مهلت {r['deadline'] or 'نامشخص'} | {kind} {where}\n  {r['url']}")
    groups = (("🌍 Overseas AI Projects", lambda r: r.get("market", "international") == "international" and r.get("line", "ai") == "ai"),
              ("🇮🇷 Iran AI Projects", lambda r: r.get("market") == "domestic" and r.get("line", "ai") == "ai"),
              ("🌐 Web Design & SEO Projects", lambda r: r.get("line") == "web"))
    for label, match in groups:
        pending = [t[i] for i in run["new_ids"] if t[i]["status"] == "new" and match(t[i])]
        if pending:
            lines.append(f"\n{label}: {len(pending)} فرصت مرتبط جدید (جزئیات و شرایط در داشبورد)")
            for r in pending[:8]:
                price = (r.get("facts") or {}).get("price", "")
                price = "" if price.startswith("در خلاصه") else f" | {price}"
                lines.append(f"• {r['country'] or '؟'} | {r['title'][:80]} | مهلت {r.get('deadline_fa') or r['deadline'] or '؟'}{price}")
    today = date.today().isoformat()
    due_items = [r for r in t.values() if r.get("status") in store.ACTIVE and (r.get("tracking") or {}).get("next_date")
                 and r["tracking"]["next_date"] <= today]
    if due_items:
        lines.append("\n🗂 پیگیری‌های سررسیدشده:")
        for r in sorted(due_items, key=lambda r: r["tracking"]["next_date"]):
            tr = r["tracking"]
            lines.append(f"• {tr['next_date']} | {tr.get('owner') or 'بدون مسئول'} | {store.STAGES.get(tr.get('stage'), '')} | "
                         f"{tr.get('next_action') or ''} – {r['title'][:60]}")
    if run["reminders"]:
        lines.append("\n⏰ یادآوری مهلت‌ها:")
        for rid in run["reminders"]:
            r = t[rid]
            lines.append(f"• {r['days_left']} روز تا مهلت: {r['title'][:70]} ({store.STATUSES[r['status']]})")
    if run.get("partner_drafts"):
        lines.append(f"\n🤝 {len(run['partner_drafts'])} پیش‌نویس پیشنهاد همکاری برای کشورهای ستاره‌دار در Drafts وب‌میل")
    if run.get("events_soon"):
        lines.append("\n📅 AI Events – ۴۵ روز آینده:")
        for e in run["events_soon"]:
            lines.append(f"• {e['start']} | {e['name_fa'] or e['name']} – {e['city']}")
    if run.get("scholarships_added"):
        lines.append(f"• {run['scholarships_added']} فرصت بورسیه‌ی جدید به فهرست اضافه شد")
    if run.get("events_added"):
        lines.append(f"• {run['events_added']} رویداد جدید به فهرست اضافه شد")
    lines.extend(run.get("papers_lines") or [])
    if run.get("leads_added"):
        lines.append(f"\n📞 {run['leads_added']} تولیدکننده‌ی بدون سایت برای تماس تلفنی (Web Design & SEO Projects)")
    if run.get("investor_drafts"):
        lines.append(f"\n✉️ {len(run['investor_drafts'])} پیش‌نویس ایمیل معرفی به سرمایه‌گذاران منتخب آماده شد")
    if run.get("investors_added"):
        lines.append(f"\n💰 {run['investors_added']} سرمایه‌گذار یا شتاب‌دهنده‌ی جدید به فهرست اضافه شد")
    url = env("DASHBOARD_URL")
    if url:
        lines.append(f"\n📊 داشبورد: {url}")
    return "\n".join(lines)


def run(use_llm=True, use_mail=True, send_notification=True):
    cfg = load_config()
    state = store.load()
    log_lines = []
    log = _log_factory(log_lines)
    seeded = store.seed_grants(state)
    if seeded:
        log(f"{seeded} grant calls added from grants_seed.json")

    profile = build_profile(cfg)
    tenders = collect_all(cfg, log)
    candidates = screen(tenders, cfg)
    log(f"{len(candidates)} tenders passed keyword screening")

    new_ids = []
    for t in candidates:
        rec, is_new = store.upsert(state, t)
        if is_new:
            new_ids.append(rec["id"])

    # expire and compute reminders over the whole pipeline
    reminders = []
    for rec in state["tenders"].values():
        rec["days_left"] = days_left(rec)
        if rec["status"] in store.ACTIVE and rec["days_left"] is not None and rec["days_left"] < 0:
            store.set_status(rec, "expired")
        elif rec["status"] in store.ACTIVE - {"new"} and rec["days_left"] in REMIND_AT:
            reminders.append(rec["id"])

    actioned, partner_drafts, events_added, papers_lines = [], [], 0, []
    pp_state = papers.load()
    ev_state, pt_state, inv_state, investors_added = events.load(), partners.load(), investors.load(), 0
    sch_state, scholarships_added = scholarships.load(), 0
    analyst = None
    if use_llm and llm_available():
        analyst = Analyst(cfg, profile_text(cfg, profile), memory.lessons_text(state))
        # Claude analysis and drafting run for the international market; domestic notices are listed from Setad data.
        queue = sorted((r for r in state["tenders"].values()
                        if r["status"] == "new" and r.get("market", "international") == "international"
                        and r.get("line", "ai") == "ai"),
                       key=lambda r: (-r.get("keyword_score", 0), r.get("days_left") or 999))
        budget = {"partner": cfg["screening"]["max_partner_packages_per_day"]}
        for rec in queue[:cfg["screening"]["max_llm_analyses_per_day"]]:
            try:
                result = process_candidate(analyst, cfg, rec, use_mail, budget, log)
                if result in ("partner_search", "bid_prep"):
                    actioned.append(rec["id"])
            except Exception as exc:
                log(f"  analysis failed for {rec['id']}: {exc}")
            store.save(state)
        # daily events refresh and weekly partner scouting for starred countries
        try:
            if events.due(ev_state, cfg):
                events_added = events.update(cfg, analyst, ev_state, log)
        except Exception as exc:
            log(f"Events update failed: {exc}")
        try:
            if scholarships.due(sch_state, cfg):
                scholarships_added = scholarships.update(cfg, analyst, sch_state, log)
        except Exception as exc:
            log(f"Scholarships update failed: {exc}")
        try:
            if papers.due(pp_state, cfg):
                papers_lines = papers.notification_lines(papers.update(cfg, analyst, pp_state, log))
        except Exception as exc:
            log(f"Papers update failed: {exc}")
        try:
            if investors.due(inv_state, cfg):
                investors_added = investors.update(cfg, analyst, inv_state, log)
        except Exception as exc:
            log(f"Investors update failed: {exc}")
        try:
            open_tenders = [r for r in state["tenders"].values() if r["status"] in store.ACTIVE]
            partner_drafts = partners.scout(cfg, analyst, pt_state, open_tenders, use_mail, log)
        except Exception as exc:
            log(f"Partner scouting failed: {exc}")
    elif use_llm:
        log("ANTHROPIC_API_KEY not set - keyword screening only, no analysis or drafts.")

    # weekly website-design leads (no Claude needed)
    lead_state, leads_added = leads.load(), 0
    try:
        if leads.due(lead_state, cfg):
            leads_added = leads.update(cfg, lead_state, log)
    except Exception as exc:
        log(f"Leads update failed: {exc}")
    leads.save(lead_state)
    # investor introduction drafts run with or without Claude (hand-written drafts need no API key)
    investor_drafts = []
    try:
        investor_drafts = investors.outreach(cfg, analyst if (use_llm and llm_available()) else None, inv_state,
                                             profile_text(cfg, profile), use_mail, log)
    except Exception as exc:
        log(f"Investor outreach failed: {exc}")
    events.save(ev_state)
    scholarships.save(sch_state)
    try:
        scholarship_docs.build_all(sch_state)
    except Exception as exc:
        log(f"Scholarship Word files failed: {exc}")
    papers.save(pp_state)
    partners.save(pt_state)
    investors.save(inv_state)
    today, soon = date.today().isoformat(), (date.today() + timedelta(days=45)).isoformat()
    events_soon = sorted((e for e in ev_state["events"].values()
                          if e.get("start") and today <= e["start"] <= soon and e.get("status") != "skipped"),
                         key=lambda e: e["start"])
    run_info = {"at": store.now(), "collected": len(tenders), "matched": len(candidates),
                "partner_drafts": partner_drafts, "events_added": events_added, "scholarships_added": scholarships_added, "investors_added": investors_added, "investor_drafts": investor_drafts, "leads_added": leads_added, "papers_lines": papers_lines,
                "events_soon": [{k: e.get(k, "") for k in ("start", "name", "name_fa", "city")} for e in events_soon],
                "new_ids": new_ids, "actioned_ids": actioned, "reminders": reminders}
    state["runs"] = (state.get("runs", []) + [run_info])[-60:]
    store.save(state)
    dashboard.render(cfg, state, run_info)

    text = summary_text(cfg, run_info, state)
    print("\n" + text)
    if send_notification:
        notify.notify(f"{cfg['agent_name_en']}: {len(actioned)} drafts, {len(new_ids)} new", text, log)
    return run_info
