"""Tender collectors. Each returns a list of normalised tender dicts:
id, source, market (international|domestic), title, description, buyer, country, deadline (YYYY-MM-DD or ''),
published, url, notice_type, facts (at-a-glance conditions known from the listing itself).
"""
import html
import re
import time
from datetime import date, timedelta

import requests

UA = {"User-Agent": "SmartCrossBorderAgent/1.0 (+https://parsaint.group)"}
TIMEOUT = 60
UNKNOWN = "در خلاصه‌ی آگهی نیامده – در اسناد مناقصه"


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


def _get(url, retries=3, **kw):
    """GET with a short retry for transient 5xx / network errors."""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=TIMEOUT, **kw)
            if r.status_code < 500:
                r.raise_for_status()
                return r
        except requests.HTTPError:
            raise
        except requests.RequestException:
            if attempt == retries - 1:
                raise
        time.sleep(3 * (attempt + 1))
    r.raise_for_status()
    return r


def _money(amount, currency):
    try:
        return f"{float(amount):,.0f} {currency}".strip()
    except (TypeError, ValueError):
        return ""


def _facts(price="", guarantee="", experience="", international=""):
    return {"price": price or UNKNOWN, "guarantee": guarantee or UNKNOWN,
            "experience": experience or UNKNOWN, "international": international or UNKNOWN}


def international_phrases(cfg):
    phrases = {p for ps in cfg["domains"].values() for p in ps}
    phrases.update(cfg.get("web_services", {}).get("keywords_en", []))
    return sorted(phrases)


TED_SECTOR = {"pub-undert": "شرکت دولتی / عمومی", "spec-rights-entity": "خصوصی (دارای حقوق ویژه)",
              "int-org": "سازمان بین‌المللی", "eu-ins-bod-ag": "نهاد اتحادیه اروپا"}


def ted_sector(types):
    for t in types or []:
        for key, label in TED_SECTOR.items():
            if str(t).startswith(key):
                return label
    return "دولتی" if types else "نامشخص"


def setad_sector(org):
    org = org or ""
    if "شرکت" in org and not any(x in org for x in ("وزارت", "سازمان", "اداره", "دانشگاه", "شهرداری")):
        return "شرکت دولتی / عمومی"
    return "دولتی"


# ---------------------------------------------------------------- TED (EU)
def fetch_ted(cfg, log):
    scfg = cfg["sources"]["ted"]
    since = (date.today() - timedelta(days=scfg["lookback_days"])).strftime("%Y%m%d")
    phrases = international_phrases(cfg)
    fields = ["publication-number", "notice-title", "buyer-name", "buyer-country",
              "deadline-receipt-tender-date-lot", "description-lot", "notice-type", "publication-date",
              "estimated-value-lot", "estimated-value-cur-lot", "procedure-type", "buyer-legal-type"]
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
                values = n.get("estimated-value-lot") or []
                cur = (n.get("estimated-value-cur-lot") or [""])[0]
                price = ""
                if values:
                    total = sum(float(v) for v in values if str(v).replace(".", "", 1).isdigit())
                    price = f"ارزش برآوردی: {_money(total, cur)}" + (f" ({len(values)} بخش)" if len(values) > 1 else "")
                results[f"TED-{pub}"] = {
                    "id": f"TED-{pub}",
                    "source": "TED (EU)",
                    "market": "international",
                    "title": _clean(_pick_lang(n.get("notice-title")), 400),
                    "description": _clean(_pick_lang(n.get("description-lot"))),
                    "buyer": _clean(_pick_lang(n.get("buyer-name")), 300),
                    "country": countries[0] if countries else "",
                    "deadline": (sorted(deadlines)[0][:10] if deadlines else ""),
                    "published": (n.get("publication-date") or "")[:10],
                    "url": f"https://ted.europa.eu/en/notice/-/detail/{pub}",
                    "notice_type": n.get("notice-type", ""),
                    "sector": ted_sector(n.get("buyer-legal-type")),
                    "facts": _facts(price=price, international=(
                        "رویه‌ی باز اتحادیه اروپا – شرکت‌های خارج از EU معمولاً مجازند مگر محدودیت صریح در اسناد"
                        if n.get("procedure-type") == "open" else "")),
                }
            if len(notices) < 100:
                break
            time.sleep(1)
    log(f"TED: {len(results)} notices")
    return list(results.values())


# ---------------------------------------------------------- World Bank
WB_TYPES = {"Request for Expression of Interest", "Invitation for Bids", "Invitation for Prequalification",
            "Request for Bids", "Request for Proposals"}


def _wb_facts(text):
    t = text.lower()
    guarantee = ""
    m = re.search(r"(bid security|bid-securing declaration|bid securing declaration)[^.]{0,200}", t)
    if m:
        guarantee = "طبق آگهی: " + m.group(0)[:200]
    experience = ""
    m = re.search(r"(shortlisting criteria|qualification requirements|qualification criteria|experience)[^.]{0,220}", t)
    if m:
        experience = "طبق آگهی: " + m.group(0)[:220]
    international = "قواعد خرید بانک جهانی: باز برای شرکت‌های همه‌ی کشورهای واجد شرایط (Eligibility rules)"
    if "national competitive" in t or "national open" in t:
        international = "رقابت ملی – احتمالاً محدود به شرکت‌های داخلی کشور خریدار"
    return guarantee, experience, international


def fetch_worldbank(cfg, log):
    rows = cfg["sources"]["worldbank"]["rows_per_query"]
    today = date.today().isoformat()
    stale_before = (date.today() - timedelta(days=45)).isoformat()
    results = {}
    for phrase in international_phrases(cfg):
        try:
            r = _get("https://search.worldbank.org/api/v2/procnotices", headers=UA,
                     params={"format": "json", "qterm": phrase, "rows": rows,
                             "srt": "submission_date", "order": "desc"})
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
            full = _clean(n.get("notice_text", ""), 20000)
            guarantee, experience, international = _wb_facts(full)
            results[f"WB-{nid}"] = {
                "id": f"WB-{nid}",
                "source": "World Bank",
                "market": "international",
                "title": _clean(n.get("bid_description") or n.get("project_name"), 400),
                "description": _clean(f"{n.get('project_name', '')}. {full}"),
                "full_text": full,
                "buyer": _clean(n.get("contact_organization"), 300),
                "country": n.get("project_ctry_name", ""),
                "deadline": deadline,
                "published": (n.get("submission_date") or "")[:10],
                "url": f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{nid}",
                "notice_type": n.get("notice_type", ""),
                "procurement_method": n.get("procurement_method_name", ""),
                "sector": "دولتی (پروژه با تأمین مالی بانک جهانی)",
                "facts": _facts(guarantee=guarantee, experience=experience, international=international),
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
            value = t.get("value") or {}
            results[f"UK-{rid}"] = {
                "id": f"UK-{rid}",
                "source": "UK Find a Tender",
                "market": "international",
                "title": _clean(t.get("title"), 400),
                "description": _clean(t.get("description")),
                "buyer": _clean((rel.get("buyer") or {}).get("name"), 300),
                "country": "United Kingdom",
                "deadline": ((t.get("tenderPeriod") or {}).get("endDate") or "")[:10],
                "published": (rel.get("date") or "")[:10],
                "url": f"https://www.find-tender.service.gov.uk/Notice/{rid}",
                "notice_type": ",".join(rel.get("tag", [])),
                "sector": "دولتی",
                "facts": _facts(
                    price=f"ارزش برآوردی: {_money(value.get('amount'), value.get('currency', 'GBP'))}" if value.get("amount") else "",
                    international="Procurement Act 2023 بریتانیا: شرکت‌های خارجی مجازند، مگر محدودیت امنیتی یا صریح"),
            }
        nxt = (data.get("links") or {}).get("next")
        if not nxt:
            break
        url, params = nxt, None
        time.sleep(0.5)
    log(f"UK FTS: {len(results)} active notices")
    return list(results.values())


# ------------------------------------------- Iran – Setad (domestic market)
def jalali_to_gregorian(jy, jm, jd):
    """Convert a Jalali (Persian calendar) date to a Gregorian date."""
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd
    days += (jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    months = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and gd > months[gm]:
        gd -= months[gm]
        gm += 1
    return date(gy, gm + 1, gd)


def _jalali_field(text):
    m = re.match(r"\s*(\d{4})/(\d{1,2})/(\d{1,2})", text or "")
    if not m:
        return ""
    try:
        return jalali_to_gregorian(*map(int, m.groups())).isoformat()
    except ValueError:
        return ""


def normalize_fa(text):
    text = (text or "").replace("ي", "ی").replace("ك", "ک").replace("‌", " ")
    return re.sub(r"\s+", " ", text)


def fetch_setad(cfg, log):
    scfg = cfg["sources"].get("setad", {})
    url = "https://gw.setadiran.ir/api/centralboard/cards/"
    headers = {**UA, "Origin": "https://fe.setadiran.ir", "Referer": "https://fe.setadiran.ir/"}
    keywords = sorted({k for ks in cfg["domestic_keywords"].values() for k in ks}
                      | set(cfg.get("web_services", {}).get("keywords_fa", [])))
    results, failures = {}, 0
    for kw in keywords:
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT,
                             params={"isLogin": "false", "userRole": 0, "keyword": kw, "pageNumber": 0,
                                     "pageSize": scfg.get("page_size", 50), "sort": "insertDate,desc"})
            r.raise_for_status()
            cards = r.json().get("content", [])
        except Exception as exc:
            failures += 1
            if failures == 1:
                log(f"Setad request failed ({kw}): {exc}")
            if failures >= 3:
                log("Setad unreachable from this network - domestic scan skipped (run it locally, see README).")
                break
            continue
        for c in cards:
            if c.get("boardName") == "مزایده":  # auctions (sales), not procurement
                continue
            number = str(c.get("number"))
            base = c.get("basePrice")
            results[f"SETAD-{number}"] = {
                "id": f"SETAD-{number}",
                "source": "ستاد (setadiran.ir)",
                "market": "domestic",
                "title": _clean(c.get("title"), 400),
                "description": _clean(f"{c.get('categoryName') or ''} – {c.get('boardName') or ''}"),
                "buyer": _clean(c.get("orgName"), 300),
                "country": "ایران" + (f" – {c.get('provinceName')}" if c.get("provinceName") else ""),
                "deadline": _jalali_field(c.get("jalaliSendDeadlineDate")),
                "deadline_fa": (c.get("jalaliSendDeadlineDate") or "").strip(),
                "published": "",
                "url": "https://fe.setadiran.ir/centralboard/#/central-board-0",
                "notice_type": c.get("boardName", ""),
                "setad_number": number,
                "sector": setad_sector(c.get("orgName")),
                "facts": _facts(
                    price=f"قیمت پایه: {base:,} ریال" if isinstance(base, (int, float)) and base else "",
                    guarantee="تضمین شرکت در فرایند ارجاع کار طبق آیین‌نامه تضمین معاملات دولتی – مبلغ در اسناد ستاد",
                    experience="ارزیابی کیفی/رتبه و سوابق طبق اسناد ستاد (نیاز به ورود به سامانه)",
                    international="نیاز به ثبت‌نام در ستاد و شخصیت حقوقی ایرانی؛ شرکت خارجی فقط از طریق شریک ایرانی"),
            }
        time.sleep(0.3)
    log(f"Setad (Iran): {len(results)} procurement notices")
    return list(results.values())


# ---------------------------------------------------- full text for analysis
def enrich_full_text(tender, log):
    """Fetch the complete notice before the LLM analysis so price, guarantee and qualification terms can be read."""
    if tender.get("full_text"):
        return tender["full_text"]
    text = ""
    try:
        if tender["id"].startswith("TED-"):
            pub = tender["id"][4:]
            r = requests.get(f"https://ted.europa.eu/en/notice/{pub}/xml", headers=UA, timeout=TIMEOUT)
            if r.ok:
                text = _clean(r.text, 25000)
        elif tender["id"].startswith("WB-"):
            r = requests.get("https://search.worldbank.org/api/v2/procnotices", headers=UA, timeout=TIMEOUT,
                             params={"format": "json", "id": tender["id"][3:], "fl": "id,notice_text"})
            notices = r.json().get("procnotices", []) if r.ok else []
            if notices:
                text = _clean(notices[0].get("notice_text", ""), 25000)
    except Exception as exc:
        log(f"  full text unavailable for {tender['id']}: {exc}")
    return text or tender.get("description", "")


# ------------------------------------- Iran – SATE research & technology demand (sate.atf.gov.ir)
def fetch_sate(cfg, log):
    """Calls for research/technology projects published by state companies and agencies in SATE
    (سامانه اجرایی تقاضا و عرضه پژوهش و فناوری). Filters from config: demand group, demand nature, live with deadline."""
    scfg = cfg["sources"]["sate"]
    base = scfg.get("url", "https://sate.atf.gov.ir").rstrip("/")
    try:
        r = _get(f"{base}/NewRequests.aspx", headers=UA)
        page = r.text
    except Exception as exc:
        log(f"SATE unreachable: {exc}")
        return []
    today = date.today().isoformat()
    group_kw, nature_eq = scfg.get("group_contains", "پژوهش"), scfg.get("nature_equals", "فناوری")
    ai_terms = [normalize_fa(x) for x in scfg.get("ai_keywords", [])]
    results, active = {}, 0
    for card in page.split('<div class="card ')[1:]:
        def field(label):
            m = re.search(re.escape(label) + r'\s*:</span>\s*<span class="text-muted">(.*?)</span>', card, re.S)
            return _clean(m.group(1), 300) if m else ""
        status = field("وضعیت تقاضا")
        if status != "فعال":
            continue
        active += 1
        m = re.search(r'href="(/Systems/Default\.aspx\?SiteRequestId=[^"]+)"[^>]*?title="([^"]+)"', card, re.S)
        if not m:
            continue
        title = html.unescape(m.group(2)).strip()
        group, nature, deadline_fa = field("گروه تقاضا"), field("ماهیت تقاضا"), field("مهلت ارسال پیشنهاده")
        deadline = _jalali_field(deadline_fa)
        if group_kw not in group or nature != nature_eq or not deadline or deadline < today:
            continue
        if ai_terms and not any(a in normalize_fa(title) for a in ai_terms):
            continue
        org = field("شرکت متقاضی")
        rid = re.sub(r"[^A-Za-z0-9]", "", m.group(1).split("=", 1)[1])
        results[f"SATE-{rid}"] = {
            "id": f"SATE-{rid}",
            "source": "ساتع (sate.atf.gov.ir)",
            "market": "domestic",
            "prefiltered": True,
            "title": title,
            "description": f"{group} – ماهیت: {nature}",
            "buyer": org,
            "country": "ایران" + (f" – {field('شهر')}" if field("شهر") else ""),
            "deadline": deadline,
            "deadline_fa": deadline_fa,
            "published": "",
            "url": base + m.group(1),
            "notice_type": f"{group} / {nature}",
            "sector": setad_sector(org),
            "facts": _facts(
                price="اعتبار پروژه‌ی پژوهشی/فناوری – مبلغ در سند نیاز ساتع",
                guarantee="طبق قرارداد پژوهشی با دستگاه متقاضی (معمولاً تضمین حسن انجام کار)",
                experience="ارسال پیشنهاده (پروپوزال) و سوابق فناور در سامانه ساتع؛ ارزیابی توسط دستگاه متقاضی",
                international="ویژه‌ی فناوران و شرکت‌های ایرانی ثبت‌نام‌شده در ساتع"),
        }
    log(f"SATE (Iran): {active} active calls, {len(results)} after filters")
    return list(results.values())


COLLECTORS = {"ted": fetch_ted, "worldbank": fetch_worldbank, "uk_fts": fetch_uk_fts, "setad": fetch_setad,
              "sate": fetch_sate}


def collect_all(cfg, log):
    tenders = []
    for name, fn in COLLECTORS.items():
        if cfg["sources"].get(name, {}).get("enabled"):
            tenders.extend(fn(cfg, log))
    return tenders
