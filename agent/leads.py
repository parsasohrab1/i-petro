"""Website-design & SEO leads: producers advertising on Iranian classified / directory sites without a website.

Only contact details that the advertiser publishes openly on its own listing are recorded - no login, no
"show number" buttons, no CAPTCHA. Requests are rate-limited, and numbers on the do-not-call list are skipped.
"""
import json
import re
import time
from datetime import date, datetime

import requests

from .config import DATA_DIR
from .sources import UA, _clean, normalize_fa

STATE_FILE = DATA_DIR / "leads.json"
STATUSES = {"new": "جدید", "called": "تماس گرفته شد", "interested": "علاقه‌مند", "proposal": "پیشنهاد قیمت",
            "won": "قرارداد", "not_interested": "علاقه‌مند نیست", "do_not_call": "تماس نگیرید"}
PRODUCER_WORDS = ["تولید", "تولیدی", "تولیدکننده", "کارخانه", "کارخانجات تولید", "صنایع", "عرضه مستقیم", "کارگاه تولید",
                  "پخش عمده", "فروش عمده", "بسته بندی", "صادرات", "سازنده"]
NOT_PRODUCER = ["تعمیر", "خدمات", "استخدام", "اجاره", "رهن", "آموزش", "دیپلم", "بازسازی", "نقاشی ساختمان"]


def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"leads": {}, "updated": "", "do_not_call": []}


def save(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def due(state, cfg):
    last = state.get("updated")
    return not last or (datetime.now() - datetime.fromisoformat(last)).days >= cfg["leads"].get("update_every_days", 7)


def _get(url):
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    return r.text


def _is_producer(text):
    t = normalize_fa(text)
    return any(w in t for w in PRODUCER_WORDS) and not any(w in t for w in NOT_PRODUCER)


# ------------------------------------------------------------------ sellfree.ir
def _sellfree_field(page, name):
    m = re.search(rf'class="darkoob{name}v"[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return ""
    text = _clean(m.group(1), 300)
    return re.sub(r"^[^:]{0,20}:\s*", "", text).strip()


def collect_sellfree(cfg, log, known):
    lcfg = cfg["leads"]["sellfree"]
    found, fetched = [], 0
    for page_no in range(1, lcfg.get("pages", 8) + 1):
        try:
            listing = _get(f"https://sellfree.ir/?page={page_no}")
        except Exception as exc:
            log(f"sellfree page {page_no} failed: {exc}")
            break
        ids = sorted(set(re.findall(r"https://sellfree\.ir/product/(\d+)", listing)))
        for pid in ids:
            key = f"sellfree-{pid}"
            if key in known or fetched >= lcfg.get("max_listings", 150):
                continue
            fetched += 1
            time.sleep(lcfg.get("delay_seconds", 1.5))
            url = f"https://sellfree.ir/product/{pid}"
            try:
                page = _get(url)
            except Exception:
                continue
            website = _sellfree_field(page, "website")
            title_m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
            title = _clean(title_m.group(1), 200) if title_m else ""
            desc = _sellfree_field(page, "desc")
            if website or not _is_producer(f"{title} {desc}"):
                continue
            mobile, tel = _sellfree_field(page, "mobile"), _sellfree_field(page, "tel")
            if not (mobile or tel):
                continue
            seller = _sellfree_field(page, "sayer").replace("صفحه اختصاصی کاربر", "").strip()
            found.append({
                "id": key, "source": "sellfree.ir", "url": url,
                "name": seller[:80] or title[:80], "activity": title, "city": _sellfree_field(page, "shahr")[:40],
                "province": _sellfree_field(page, "ostan")[:40],
                "phone": " / ".join(dict.fromkeys(x for x in (mobile, tel) if x)), "email": _sellfree_field(page, "mail")[:80],
                "website": "", "service_fa": "طراحی سایت + سئو",
            })
        if fetched >= lcfg.get("max_listings", 150):
            break
    log(f"sellfree: {fetched} listings checked, {len(found)} producers without website")
    return found


# ------------------------------------------------------------------ abcagahi.ir
def collect_abcagahi(cfg, log, known):
    """abcagahi shows numbers only after login, so leads are recorded with the listing link only."""
    lcfg = cfg["leads"]["abcagahi"]
    found, titles = [], set()
    for page_no in range(1, lcfg.get("pages", 3) + 1):
        url = "https://abcagahi.ir/" if page_no == 1 else f"https://abcagahi.ir/?start={(page_no - 1) * 20}"
        try:
            html_text = _get(url)
        except Exception as exc:
            log(f"abcagahi page {page_no} failed: {exc}")
            break
        for m in re.finditer(r'href="(/ad/([^"]+)-(\d+))"', html_text):
            href, slug, num = m.groups()
            key = f"abcagahi-{num}"
            title = requests.utils.unquote(slug).replace("-", " ")
            if key in known or title in titles or not _is_producer(title):
                continue
            titles.add(title)
            phones = list(dict.fromkeys(re.findall(r"09\d{9}", title)))  # numbers the advertiser put in its own ad title
            found.append({
                "id": key, "source": "abcagahi.ir", "url": "https://abcagahi.ir" + href,
                "name": "", "activity": re.sub(r"09\d{9}", "", title).strip()[:200], "city": "", "province": "",
                "phone": " / ".join(phones), "email": "", "website": "",
                "contact_note_fa": "" if phones else "شماره فقط پس از ورود نمایش داده می‌شود – تماس از داخل سایت",
                "service_fa": "طراحی سایت + سئو",
            })
        time.sleep(lcfg.get("delay_seconds", 1.5))
    log(f"abcagahi: {len(found)} producer listings (contact via site)")
    return found


COLLECTORS = {"sellfree": collect_sellfree, "abcagahi": collect_abcagahi}


def update(cfg, state, log):
    known = set(state["leads"])
    blocked = {re.sub(r"\D", "", n) for n in state.get("do_not_call", [])}
    added = 0
    for name, fn in COLLECTORS.items():
        if not cfg["leads"].get(name, {}).get("enabled"):
            continue
        try:
            for lead in fn(cfg, log, known):
                digits = {re.sub(r"\D", "", p) for p in lead["phone"].split("/") if p.strip()}
                if digits & blocked:
                    continue
                state["leads"][lead["id"]] = {**lead, "status": "new", "found": date.today().isoformat()}
                known.add(lead["id"])
                added += 1
        except Exception as exc:
            log(f"Leads collector {name} failed: {exc}")
    state["updated"] = datetime.now().isoformat(timespec="seconds")
    return added
