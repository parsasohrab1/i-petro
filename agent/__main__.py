"""CLI.

  python -m agent run [--no-llm] [--no-mail] [--no-notify]   daily run
  python -m agent list [--all]                              pipeline overview
  python -m agent status <tender-id> <status> [note...]      move a tender along the pipeline
  python -m agent redo <tender-id>                           re-analyse and re-draft one tender
  python -m agent dashboard                                  rebuild docs/index.html
  python -m agent star <country> / unstar <country>          countries for weekly partner scouting
  python -m agent event <event-id> <status>                  considering | registered | attending | attended | skipped
  python -m agent partner <company-key> <status>             sent | replied | meeting | mou | not_interested
  python -m agent investor <investor-id> <status>            researching | contacted | meeting | due_diligence | term_sheet | declined
"""
import json
import argparse
import sys

from . import dashboard, events, investors, partners, store
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
    for name in ("star", "unstar"):
        sub.add_parser(name).add_argument("country")
    ev = sub.add_parser("event")
    ev.add_argument("event_id")
    ev.add_argument("status", choices=list(events.STATUSES))
    pa = sub.add_parser("partner")
    pa.add_argument("key")
    pa.add_argument("status", choices=list(partners.STATUSES))
    iv = sub.add_parser("investor")
    iv.add_argument("investor_id")
    iv.add_argument("status", choices=list(investors.STATUSES))
    a = p.parse_args(argv)

    if a.cmd == "run":
        from .pipeline import run
        run(use_llm=not a.no_llm, use_mail=not a.no_mail, send_notification=not a.no_notify)
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
        analyst = Analyst(cfg, profile_text(cfg, build_profile(cfg)))
        process_candidate(analyst, cfg, rec, True, {"partner": 1}, print)
        store.save(state)
        dashboard.render(cfg, state)
    elif a.cmd == "dashboard":
        print(dashboard.render(cfg, state))


if __name__ == "__main__":
    main()
