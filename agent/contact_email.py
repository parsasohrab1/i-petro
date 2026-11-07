"""Finds a company's generic business address by reading its own website (home page and the usual contact pages).
Only addresses published on the company's own domain and with a generic mailbox name (info@, contact@, sales@ ...)
are returned; personal addresses are never collected and nothing is guessed."""
import html
import re
import time
from urllib.parse import urljoin, urlparse

import requests

UA = {"User-Agent": "SmartCrossBorderAgent/1.0 (+https://parsaint.group)"}
TIMEOUT = 20
MAX_PAGES = 7
CONTACT_PATHS = ("/contact", "/contact-us", "/contacts", "/contactus", "/about", "/about-us", "/en/contact",
                 "/impressum", "/kontakt", "/iletisim", "/contacto")
CONTACT_HINT = re.compile(r"contact|kontakt|about|impressum|iletisim|contacto|reach|enquir|inquir|partner", re.I)
GENERIC = ("info", "contact", "contacts", "hello", "office", "sales", "enquiries", "enquiry", "inquiries", "inquiry",
           "partnerships", "partners", "partner", "business", "bd", "tenders", "tender", "procurement", "mail",
           "admin", "general", "marketing", "support", "service", "team", "iletisim", "kontakt", "contacto", "bilgi")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
OBFUSCATED = re.compile(r"([A-Za-z0-9._%+-]+)\s*[\[\(]\s*at\s*[\]\)]\s*([A-Za-z0-9-]+(?:\s*[\[\(]\s*dot\s*[\]\)]\s*[A-Za-z0-9-]+)+)", re.I)
CFEMAIL = re.compile(r'data-cfemail="([0-9a-f]+)"')
BAD_TLD = {"png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js", "woff", "woff2"}


def _host(url):
    h = urlparse(url if "//" in url else "https://" + url).netloc.lower().split(":")[0]
    return h.removeprefix("www.")


def _same_domain(email, host):
    d = email.split("@")[-1].lower()
    return d == host or d.endswith("." + host) or host.endswith("." + d) or d.split(".")[-2:] == host.split(".")[-2:]


def _decode_cf(hexstr):
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def extract_emails(page):
    """All address-looking strings on a page, including mailto: links, '[at]/[dot]' spellings and Cloudflare-protected ones."""
    text = html.unescape(page)
    found = [m for m in EMAIL.findall(text)]
    found += [_decode_cf(h) for h in CFEMAIL.findall(text)]
    for user, dom in OBFUSCATED.findall(text):
        found.append(user + "@" + re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", dom, flags=re.I).replace(" ", ""))
    out = []
    for e in found:
        e = e.strip(".,;:").lower()
        if "@" in e and e.rsplit(".", 1)[-1] not in BAD_TLD and e not in out:
            out.append(e)
    return out


def _rank(email):
    """Position in GENERIC when the mailbox name is a generic one (info, sales2 ...), else None."""
    local = email.split("@")[0].replace("-", "").replace("_", "").replace(".", "")
    for i, g in enumerate(GENERIC):
        if local == g or (local.startswith(g) and local[len(g):].isdigit()):
            return i
    return None


def is_generic(email):
    return _rank(email) is not None


def _get(url, session):
    try:
        r = session.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200 and "html" in r.headers.get("content-type", "html").lower():
            return r.text
    except requests.RequestException:
        pass
    return ""


def find_email(website, log=lambda m: None, delay=1.0):
    """Returns (email, source_url) or ("", "")."""
    if not website:
        return "", ""
    base = website if "//" in website else "https://" + website
    host, session, seen, queue = _host(base), requests.Session(), set(), [base]
    candidates = []   # (rank, email, url)
    while queue and len(seen) < MAX_PAGES:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        page = _get(url, session)
        if not page:
            continue
        for e in extract_emails(page):
            if _same_domain(e, host) and is_generic(e):
                candidates.append((_rank(e), e, url))
        if candidates:
            break
        if len(seen) == 1:   # discover contact pages: linked ones first, then the usual paths
            links = re.findall(r'href=["\']([^"\'#]+)["\']', page, re.I)
            linked = [urljoin(url, l) for l in links if CONTACT_HINT.search(l) and not l.lower().startswith(("mailto:", "tel:"))]
            queue += [u for u in linked if _host(u) == host][:4] + [urljoin(base, p) for p in CONTACT_PATHS]
        time.sleep(delay)
    if not candidates:
        log(f"  no published generic address found on {host}")
        return "", ""
    candidates.sort(key=lambda c: c[0])
    _, email, src = candidates[0]
    log(f"  {host}: {email} (from {src})")
    return email, src
