"""Cheap rule-based pre-screen so only promising tenders reach the (paid) LLM analysis."""
from datetime import date


def keyword_score(tender, cfg):
    title = tender["title"].lower()
    body = f"{tender['title']} {tender['description']}".lower()
    if any(x in title for x in cfg["exclude_keywords"]):
        return 0, []
    score, domains = 0, set()
    for domain, phrases in cfg["domains"].items():
        for p in phrases:
            p = p.lower()
            if p in title:
                score += 3
                domains.add(domain)
            elif p in body:
                score += 1
                domains.add(domain)
    return score, sorted(domains)


def days_left(tender):
    if not tender.get("deadline"):
        return None
    try:
        return (date.fromisoformat(tender["deadline"]) - date.today()).days
    except ValueError:
        return None


def screen(tenders, cfg):
    """Return candidates sorted best-first, each annotated with keyword_score, domains and days_left."""
    scfg = cfg["screening"]
    out = []
    for t in tenders:
        score, domains = keyword_score(t, cfg)
        left = days_left(t)
        if score < scfg["min_keyword_score"]:
            continue
        if left is not None and left < scfg["min_days_to_deadline"]:
            continue
        out.append({**t, "keyword_score": score, "domains": domains, "days_left": left})
    out.sort(key=lambda t: (-t["keyword_score"], t["days_left"] if t["days_left"] is not None else 999))
    return out
