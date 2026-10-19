"""Cheap rule-based pre-screen so only promising tenders reach the (paid) LLM analysis.
International tenders are matched with English keywords, domestic (Iran) tenders with Persian keywords."""
from datetime import date

from .sources import normalize_fa


def _keyword_sets(tender, cfg):
    if tender.get("market") == "domestic":
        return cfg["domestic_keywords"], cfg.get("domestic_exclude_keywords", []), normalize_fa
    return cfg["domains"], cfg["exclude_keywords"], str


def web_hit(tender, cfg):
    """Website design / SEO requests go to the separate web-services tab."""
    web = cfg.get("web_services", {})
    domestic = tender.get("market") == "domestic"
    words = web.get("keywords_fa" if domestic else "keywords_en", [])
    norm = normalize_fa if domestic else str
    title = norm(tender["title"]).lower()
    return any(norm(w).lower() in title for w in words)


def keyword_score(tender, cfg):
    if tender.get("prefiltered"):  # SATE notices are filtered at the source (research / technology / live / AI)
        return 3, ["ai_cross_cutting"]
    domains_map, exclude, norm = _keyword_sets(tender, cfg)
    title = norm(tender["title"]).lower()
    body = norm(f"{tender['title']} {tender['description']}").lower()
    if any(norm(x).lower() in title for x in exclude):
        return 0, []
    if web_hit(tender, cfg):
        return 3, ["web"]
    required = cfg.get("domestic_required_any") if tender.get("market") == "domestic" else None
    if required and not any(norm(x).lower() in title for x in required):
        return 0, []  # domestic notices must name a technology scope, not only a sector
    score, domains = 0, set()
    for domain, phrases in domains_map.items():
        for p in phrases:
            p = norm(p).lower()
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
        min_days = scfg["min_days_to_deadline"] if t.get("market") != "domestic" else scfg.get("min_days_domestic", 2)
        if score < scfg["min_keyword_score"]:
            continue
        if left is not None and left < min_days:
            continue
        line = "web" if domains == ["web"] else "ai"
        out.append({**t, "keyword_score": score, "domains": domains, "days_left": left, "line": line})
    out.sort(key=lambda t: (-t["keyword_score"], t["days_left"] if t["days_left"] is not None else 999))
    return out
