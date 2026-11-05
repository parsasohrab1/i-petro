"""Ad-hoc search of TED (EU) and the World Bank procurement notices, with a preset for international health-AI projects.

  python -m agent search "digital pathology" "AI screening" [--source ted|worldbank|all] [--days 30] [--add]
  python -m agent search --health [--days 30] [--add]

Without --add nothing is stored: the hits are only printed. With --add the hits that pass the same keyword screening as the
daily run are put into the tender pipeline (status "new") so they show up in Overseas AI Projects after the next platform sync."""
import copy

from . import store
from .screening import days_left, screen
from .sources import fetch_ted, fetch_worldbank

SOURCES = ("ted", "worldbank")


def health_phrases(cfg):
    return list(cfg["domains"].get("health_ai", []))


def _adhoc_cfg(cfg, phrases, days):
    c = copy.deepcopy(cfg)
    c["domains"] = {"adhoc": list(phrases)}
    c["web_services"] = {**c.get("web_services", {}), "keywords_en": []}
    c["sources"]["ted"].update({"lookback_days": days, "max_pages": 2})
    return c


def search(cfg, phrases, sources=SOURCES, days=30, log=print):
    """Return the raw notices from the chosen sources for the given phrases (not screened, not stored)."""
    c = _adhoc_cfg(cfg, phrases, days)
    out = []
    if "ted" in sources:
        out.extend(fetch_ted(c, log))
    if "worldbank" in sources:
        out.extend(fetch_worldbank(c, log))
    return out


def add_to_pipeline(cfg, hits, log=print):
    """Screen the hits like the daily run does and upsert the survivors; returns the new tender ids."""
    state = store.load()
    new_ids = []
    for t in screen(hits, cfg):
        rec, is_new = store.upsert(state, t)
        if is_new:
            new_ids.append(rec["id"])
    for rec in state["tenders"].values():
        rec["days_left"] = days_left(rec)
    store.save(state)
    log(f"{len(new_ids)} new tender(s) added to the pipeline")
    return new_ids


def format_hit(t):
    return f"{t['id']:<22} {t.get('deadline') or '?':<11} {t.get('country', '')[:12]:<12} {t['title'][:90]}"
