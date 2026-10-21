"""Learning memory: decided tenders (won / lost / dropped) and the reasons the team recorded on the platform.

`lessons_text` turns them into a short block that is appended to the analyst's system prompt, so the next
relevance and eligibility judgements take the team's own track record into account.
"""

OUTCOMES = {"won": "WON", "lost": "LOST", "dropped": "DROPPED (team decided not to bid)"}


def decided(state):
    """Tenders with an outcome recorded in tracking (platform) or a final pipeline status."""
    out = []
    for t in state["tenders"].values():
        tr = t.get("tracking") or {}
        outcome = tr.get("outcome") or {"won": "won", "lost": "lost", "skipped": "dropped"}.get(t.get("status"), "")
        if outcome:
            out.append((t, outcome, (tr.get("outcome_reason") or "").strip()))
    return out


def lessons_text(state, limit=25):
    rows = decided(state)
    if not rows:
        return ""
    rows.sort(key=lambda r: (r[0].get("tracking") or {}).get("updated", ""), reverse=True)
    lines = []
    for t, outcome, reason in rows[:limit]:
        a = t.get("analysis") or {}
        lines.append(f"- {OUTCOMES[outcome]}: {t.get('title', '')[:110]} | {t.get('country', '')} | buyer {t.get('buyer', '')[:60]} | "
                     f"eligibility {a.get('eligibility', '?')} | relevance {a.get('relevance_score', '?')} | reason: {reason or 'not recorded'}")
    return ("\n\nTEAM MEMORY (outcomes and reasons recorded by the team on earlier tenders; use them to calibrate "
            "relevance, eligibility and effort, but never to invent facts):\n" + "\n".join(lines))
