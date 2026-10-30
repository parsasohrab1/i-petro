"""CLI.

  python -m agent run [--no-llm] [--no-mail] [--no-notify]   daily run
  python -m agent list [--all]                              pipeline overview
  python -m agent status <tender-id> <status> [note...]      move a tender along the pipeline
  python -m agent redo <tender-id>                           re-analyse and re-draft one tender
  python -m agent dashboard                                  rebuild docs/index.html
  python -m agent star <country> / unstar <country>          countries for weekly partner scouting
  python -m agent event <event-id> <status>                  considering | registered | attending | attended | skipped
  python -m agent scholarship [--no-llm] [--set ID STATUS]     refresh fully funded scholarships and rebuild the Word files
  python -m agent partner <company-key> <status>             sent | replied | meeting | mou | not_interested
  python -m agent select <investor-id> / unselect <investor-id>  investors that get an introduction draft
  python -m agent lead <lead-id> <status>                    called | interested | proposal | won | not_interested | do_not_call
  python -m agent track <tender-id> [--owner NAME] [--stage STAGE] [--next TEXT] [--date YYYY-MM-DD] [--note TEXT]
      stages: identified | documents | partner_email | partner_meeting | mou | proposal | submitted | result
  python -m agent remind-reports <folder>                    Telegram reminder to members without today's performance report
  python -m agent save-drafts <zip|folder|file.eml>          put .eml drafts (e.g. the partners-tab ZIP) into the parsaint.group Drafts folder
  python -m agent investor <investor-id> <status>            researching | contacted | meeting | due_diligence | term_sheet | declined
"""
import json
import argparse
import sys

from pathlib import Path

from . import dashboard, events, investors, leads, memory, partners, platform_sync, platform_sch, scholarship_docs, scholarships, store
from .config import ROOT, load_config


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="agent")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--no-llm", action="store_true")
    r.add_argument("--no-mail", action="store_true")
    r.add_argument("--no-notify", action="store_true")
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true")
    st = sub.add_parser("status")
    st.add_argument("tender_id")
    st.add_argument("status", choices=list(store.STATUSES))
    st.add_argument("note", nargs="*")
    rd = sub.add_parser("redo")
    rd.add_argument("tender_id")
    sub.add_parser("dashboard")
    for name in ("select", "unselect"):
        sub.add_parser(name).add_argument("investor_id")
    for name in ("star", "unstar"):
        sub.add_parser(name).add_argument("country")
    ev = sub.add_parser("event")
    ev.add_argument("event_id")
    ev.add_argument("status", choices=list(events.STATUSES))
    sc = sub.add_parser("scholarship")
    sc.add_argument("--no-llm", action="store_true")
    sc.add_argument("--set", nargs=2, metavar=("ID", "STATUS"))
    pa = sub.add_parser("partner")
    pa.add_argument("key")
    pa.add_argument("status", choices=list(partners.STATUSES))
    tk = sub.add_parser("track")
    tk.add_argument("tender_id")
    tk.add_argument("--owner")
    tk.add_argument("--stage", choices=list(store.STAGES))
    tk.add_argument("--next", dest="next_action")
    tk.add_argument("--date", dest="next_date")
    tk.add_argument("--note", default="")
    rr = sub.add_parser("remind-reports")
    rr.add_argument("folder")
    sd = sub.add_parser("save-drafts")
    sd.add_argument("source")
    ld = sub.add_parser("lead")
    ld.add_argument("lead_id")
    ld.add_argument("status", choices=list(leads.STATUSES))
    iv = sub.add_parser("investor")
    iv.add_argument("investor_id")
    iv.add_argument("status", choices=list(investors.STATUSES))
    se = sub.add_parser("search")
    se.add_argument("terms", nargs="*")
    se.add_argument("--health", action="store_true", help="use the international health-AI phrase list")
    se.add_argument("--source", choices=("ted", "worldbank", "all"), default="all")
    se.add_argument("--days", type=int, default=30, help="TED look-back in days")
    se.add_argument("--add", action="store_true", help="put hits that pass keyword screening into the pipeline")
    a = p.parse_args(argv)

    if a.cmd == "search":
        from . import search as srch
        cfg = load_config()
        phrases = srch.health_phrases(cfg) if a.health else []
        phrases += a.terms
        if not phrases:
            sys.exit("give search terms or --health")
        hits = srch.search(cfg, phrases, srch.SOURCES if a.source == "all" else (a.source,), a.days)
        for t in sorted(hits, key=lambda t: t.get("deadline") or "9"):
            print(srch.format_hit(t))
        print(f"{len(hits)} notice(s)")
        if a.add:
            srch.add_to_pipeline(cfg, hits)
        return

    if a.cmd == "run":
        from .pipeline import run
        run(use_llm=not a.no_llm, use_mail=not a.no_mail, send_notification=not a.no_notify)
        return

    if a.cmd == "save-drafts":
        from . import mailbox
        if not mailbox.configured():
            sys.exit("Set IMAP_HOST, IMAP_USER and IMAP_PASSWORD in .env first (see .env.example).")
        cfg, n = load_config(), 0
        for name, msg in mailbox.drafts_from_eml(a.source):
            folder = mailbox.save_draft(msg, cfg)
            n += 1
            print(f"{name} -> {folder} (To: {msg['To'] or '-'})")
        print(f"{n} draft(s) saved to the parsaint.group mailbox. Nothing was sent.")
        return

    cfg, state = load_config(), store.load()
    if a.cmd in ("star", "unstar"):
        stars = cfg.setdefault("starred_countries", [])
        if a.cmd == "star" and a.country not in stars:
            stars.append(a.country)
        if a.cmd == "unstar" and a.country in stars:
            stars.remove(a.country)
        (ROOT / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        dashboard.render(cfg, state)
        print("starred countries:", ", ".join(stars) or "-")
        return
    if a.cmd == "event":
        es = events.load()
        if a.event_id not in es["events"]:
            sys.exit(f"unknown event {a.event_id}")
        events.set_status(es, a.event_id, a.status)
        events.save(es)
        dashboard.render(cfg, state)
        print(f"{a.event_id} -> {events.STATUSES[a.status]}")
        return
    if a.cmd == "partner":
        ps = partners.load()
        if a.key not in ps["companies"]:
            sys.exit(f"unknown company {a.key}")
        ps["companies"][a.key]["status"] = a.status
        partners.save(ps)
        dashboard.render(cfg, state)
        print(f"{a.key} -> {partners.STATUSES[a.status]}")
        return
    if a.cmd == "scholarship":
        ss = scholarships.load()
        if a.set:
            if a.set[0] not in ss["scholarships"]:
                sys.exit(f"unknown scholarship {a.set[0]}")
            scholarships.set_status(ss, *a.set)
        elif not a.no_llm:
            from .analyst import Analyst, llm_available
            from .portfolio import build_profile, profile_text
            if llm_available():
                analyst = Analyst(cfg, profile_text(cfg, build_profile(cfg)), memory.lessons_text(state))
                scholarships.update(cfg, analyst, ss, print)
            else:
                print("ANTHROPIC_API_KEY not set - rebuilding the Word files from the stored list only.")
        scholarships.save(ss)
        for path in scholarship_docs.build_all(ss):
            print(path)
        print(f"dashboard page: {platform_sch.sync(ss)} scholarships synced")
        return
    if a.cmd in ("select", "unselect"):
        chosen = cfg.setdefault("selected_investors", [])
        if a.investor_id not in investors.load()["investors"]:
            sys.exit(f"unknown investor {a.investor_id}")
        if a.cmd == "select" and a.investor_id not in chosen:
            chosen.append(a.investor_id)
        if a.cmd == "unselect" and a.investor_id in chosen:
            chosen.remove(a.investor_id)
        (ROOT / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        dashboard.render(cfg, state)
        print("selected investors:", ", ".join(chosen) or "-")
        return
    if a.cmd == "track":
        rec = state["tenders"].get(a.tender_id)
        if not rec:
            sys.exit(f"unknown tender {a.tender_id}")
        tr = store.track(rec, a.owner, a.stage, a.next_action, a.next_date, a.note)
        store.save(state)
        dashboard.render(cfg, state)
        print(f"{a.tender_id}: {tr.get('owner') or '-'} | {store.STAGES[tr['stage']]} | {tr.get('next_action') or '-'} {tr.get('next_date') or ''}")
        return
    if a.cmd == "remind-reports":
        missing = platform_sync.report_reminders(Path(a.folder), log=print)
        print("Missing today: " + (", ".join(missing) if missing else "nobody"))
        return
    if a.cmd == "lead":
        ls_ = leads.load()
        if a.lead_id not in ls_["leads"]:
            sys.exit(f"unknown lead {a.lead_id}")
        rec = ls_["leads"][a.lead_id]
        rec["status"] = a.status
        if a.status == "do_not_call":
            ls_.setdefault("do_not_call", []).extend(p.strip() for p in rec.get("phone", "").split("/") if p.strip())
            rec["phone"] = ""
        leads.save(ls_)
        dashboard.render(cfg, state)
        print(f"{a.lead_id} -> {leads.STATUSES[a.status]}")
        return
    if a.cmd == "investor":
        ist = investors.load()
        if a.investor_id not in ist["investors"]:
            sys.exit(f"unknown investor {a.investor_id}")
        ist["investors"][a.investor_id]["status"] = a.status
        investors.save(ist)
        dashboard.render(cfg, state)
        print(f"{a.investor_id} -> {investors.STATUSES[a.status]}")
        return
    if a.cmd == "list":
        for t in sorted(state["tenders"].values(), key=lambda t: t.get("deadline") or "9"):
            if a.all or t["status"] in store.ACTIVE:
                score = (t.get("analysis") or {}).get("relevance_score", "-")
                print(f"{t['id']:<28} {store.STATUSES[t['status']]:<26} {t.get('deadline') or '?':<11} "
                      f"{score!s:<4} {t['country'][:14]:<14} {t['title'][:70]}")
    elif a.cmd == "status":
        rec = state["tenders"].get(a.tender_id)
        if not rec:
            sys.exit(f"unknown tender {a.tender_id}")
        store.set_status(rec, a.status, " ".join(a.note))
        store.save(state)
        dashboard.render(cfg, state)
        print(f"{a.tender_id} -> {store.STATUSES[a.status]}")
    elif a.cmd == "redo":
        from .analyst import Analyst
        from .pipeline import process_candidate
        from .portfolio import build_profile, profile_text
        rec = state["tenders"].get(a.tender_id)
        if not rec:
            sys.exit(f"unknown tender {a.tender_id}")
        analyst = Analyst(cfg, profile_text(cfg, build_profile(cfg)), memory.lessons_text(state))
        process_candidate(analyst, cfg, rec, True, {"partner": 1}, print)
        store.save(state)
        dashboard.render(cfg, state)
    elif a.cmd == "dashboard":
        print(dashboard.render(cfg, state))


if __name__ == "__main__":
    main()
