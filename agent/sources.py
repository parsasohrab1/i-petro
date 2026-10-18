"""Tender collectors. Each returns a list of normalised tender dicts:
id, source, title, description, buyer, country, deadline (YYYY-MM-DD or ''), published, url, notice_type.
"""
import html
import re
import time
from datetime import date, timedelta

import requests

UA = {"User-Agent": "SmartCrossBorderAgent/1.0 (+https://parsaint.group)"}
TIMEOUT = 60


def _clean(text, limit=4000):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _pick_lang(value):
    """TED returns {lang: text} or {lang: [text, ...]}; prefer English."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value:
        chosen = value.get("eng") or next(iter(value.values()))
        if isinstance(chosen, list):
            return " ".join(str(x) for x in chosen)
        return str(chosen)
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return ""


def _all_phrases(cfg):
    return sorted({p for phrases in cfg["domains"].values() for p in phrases})


# ---------------------------------------------------------------- TED (EU)
def fetch_ted(cfg, log):
    scfg = cfg["sources"]["ted"]
    since = (date.today() - timedelta(days=scfg["lookback_days"])).strftime("%Y%m%d")
    phrases = _all_phrases(cfg)
    fields = ["publication-number", "notice-title", "buyer-name", "buyer-country",
              "deadline-receipt-tender-date-lot", "description-lot", "notice-type", "publication-date"]
    results = {}
    # TED's expert query has a length limit, so phrases are sent in small groups.
    for i in range(0, len(phrases), 8):
        group = phrases[i:i + 8]
        ft = " OR ".join(f'FT~"{p}"' for p in group)
        query = f"({ft}) AND PD>={since} AND notice-type IN (cn-standard cn-social cn-desg pin-cfc-standard)"
        for page in range(1, scfg["max_pages"] + 1):
            try:
                r = requests.post("https://api.ted.europa.eu/v3/notices/search", headers=UA, timeout=TIMEOUT,
                                  json={"query": query, "fields": fields, "limit": 100, "page": page})
                r.raise_for_status()
                notices = r.json().get("notices", [])
            except Exception as exc:  # one failing group must not stop the run
                log(f"TED query failed ({group[0]}...): {exc}")
                break
            for n in notices:
                pub = n.get("publication-number")
                deadlines = n.get("deadline-receipt-tender-date-lot") or []
                countries = n.get("buyer-country") or []
                results[f"TED-{pub}"] = {
                    "id": f"TED-{pub}",
                    "source": "TED (EU)",
                    "title": _clean(_pick_lang(n.get("notice-title")), 400),
                    "description": _clean(_pick_lang(n.get("description-lot"))),
                    "buyer": _clean(_pick_lang(n.get("buyer-name")), 300),
                    "country": countries[0] if countries else "",
                    "deadline": (sorted(deadlines)[0][:10] if deadlines else ""),
                    "published": (n.get("publication-date") or "")[:10],
                    "url": f"https://ted.europa.eu/en/notice/-/detail/{pub}",
                    "notice_type": n.get("notice-type", ""),
                }
            if len(notices) < 100:
                break
            time.sleep(1)
    log(f"TED: {len(results)} notices")
    return list(results.values())


# ---------------------------------------------------------- World Bank
WB_TYPES = {"Request for Expression of Interest", "Invitation for Bids", "Invitation for Prequalification",
            "Request for Bids", "Request for Proposals"}


def fetch_worldbank(cfg, log):
    rows = cfg["sources"]["worldbank"]["rows_per_query"]
    today = date.today().isoformat()
    stale_before = (date.today() - timedelta(days=45)).isoformat()
    results = {}
    for phrase in _all_phrases(cfg):
        try:
            r = requests.get("https://search.worldbank.org/api/v2/procnotices", headers=UA, timeout=TIMEOUT,
                             params={"format": "json", "qterm": phrase, "rows": rows,
                                     "srt": "submission_date", "order": "desc"})
            r.raise_for_status()
            notices = r.json().get("procnotices", [])
        except Exception as exc:
            log(f"World Bank query failed ({phrase}): {exc}")
            continue
        for n in notices:
            deadline = (n.get("submission_deadline_date") or "")[:10]
            if n.get("notice_type") not in WB_TYPES or n.get("notice_status") != "Published":
                continue
            if deadline and deadline < today:
                continue
            if not deadline and (n.get("submission_date") or "")[:10] < stale_before:
                continue  # old notices that carry no deadline
            nid = n.get("id")
            results[f"WB-{nid}"] = {
                "id": f"WB-{nid}",
                "source": "World Bank",
                "title": _clean(n.get("bid_description") or n.get("project_name"), 400),
                "description": _clean(f"{n.get('project_name', '')}. {n.get('notice_text', '')}"),
                "buyer": _clean(n.get("contact_organization"), 300),
                "country": n.get("project_ctry_name", ""),
                "deadline": deadline,
                "published": (n.get("submission_date") or "")[:10],
                "url": f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{nid}",
                "notice_type": n.get("notice_type", ""),
                "procurement_method": n.get("procurement_method_name", ""),
            }
        time.sleep(0.5)
    log(f"World Bank: {len(results)} open notices")
    return list(results.values())


# ------------------------------------------------------ UK Find a Tender
def fetch_uk_fts(cfg, log):
    scfg = cfg["sources"]["uk_fts"]
    since = (date.today() - timedelta(days=scfg["lookback_days"])).isoformat() + "T00:00:00"
    url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"
    params = {"limit": 100, "stages": "tender", "updatedFrom": since}
    results = {}
    for _ in range(scfg["max_pages"]):
        try:
            r = requests.get(url, headers=UA, timeout=TIMEOUT, params=params)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log(f"UK FTS request failed: {exc}")
            break
        for rel in data.get("releases", []):
            t = rel.get("tender", {})
            if t.get("status") not in (None, "active", "planning"):
                continue
            rid = rel.get("id", "")
            results[f"UK-{rid}"] = {
                "id": f"UK-{rid}",
                "source": "UK Find a Tender",
                "title": _clean(t.get("title"), 400),
                "description": _clean(t.get("description")),
                "buyer": _clean((rel.get("buyer") or {}).get("name"), 300),
                "country": "United Kingdom",
                "deadline": ((t.get("tenderPeriod") or {}).get("endDate") or "")[:10],
                "published": (rel.get("date") or "")[:10],
                "url": f"https://www.find-tender.service.gov.uk/Notice/{rid}",
                "notice_type": ",".join(rel.get("tag", [])),
            }
        nxt = (data.get("links") or {}).get("next")
        if not nxt:
            break
        url, params = nxt, None
        time.sleep(0.5)
    log(f"UK FTS: {len(results)} active notices")
    return list(results.values())


COLLECTORS = {"ted": fetch_ted, "worldbank": fetch_worldbank, "uk_fts": fetch_uk_fts}


def collect_all(cfg, log):
    tenders = []
    for name, fn in COLLECTORS.items():
        if cfg["sources"].get(name, {}).get("enabled"):
            tenders.extend(fn(cfg, log))
    return tenders
