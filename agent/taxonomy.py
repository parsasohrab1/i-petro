"""Sector taxonomy. The old "energy" group is split into five sectors:
oil_gas (نفت و گاز), aerospace (هوا فضا), nuclear (هسته‌ای), water (آب), mining (معدن).
Medical, urban and ai_cross_cutting stay as they were. Legacy keys ("energy", "aviation") are mapped on load so cached
data from earlier runs, hand-written seeds and model answers all end up on the new keys."""
import re

SECTORS = ["oil_gas", "aerospace", "nuclear", "water", "mining"]
LABELS_FA = {"oil_gas": "نفت و گاز", "aerospace": "هوا فضا", "nuclear": "هسته‌ای", "water": "آب", "mining": "معدن"}

_NUC = re.compile(r"nuclear|reactor|radiation|uranium|هسته|راکتور|پرتو", re.I)
_MIN = re.compile(r"\bmining\b|\bmines?\b|mineral|\bores?\b|quarr(?:y|ies)|metallurg|smelt|copper|iron ore|معدن|سنگ آهن|فولاد|کانی", re.I)
_WAT = re.compile(r"water|aquifer|wastewater|desalin|hydrolog|irrigat|dam safety|آبخوان|فاضلاب|شیرین‌سازی|(?:^|\W)آب(?!\w)", re.I)
_AER = re.compile(r"aero|aviation|aircraft|airport|airline|flight|space|satellite|uav|drone|هوافضا|هواپیما|فرودگاه|پرواز|ماهواره", re.I)


def sector_of_text(text):
    """Best sector for a free text (used for legacy 'energy' records). Generic energy (power, grid, solar) goes to oil_gas."""
    if _NUC.search(text):
        return "nuclear"
    if _MIN.search(text):
        return "mining"
    if _AER.search(text):
        return "aerospace"
    if _WAT.search(text):
        return "water"
    return "oil_gas"


def canon_domains(domains, text=""):
    """Map a list of domain keys onto the new taxonomy, keeping order and removing duplicates."""
    out = []
    for d in domains or []:
        if d == "energy":
            d = sector_of_text(text)
        elif d == "aviation":
            d = "aerospace"
        if d not in out:
            out.append(d)
    return out


def canon_record(rec, key):
    """Normalise rec[key] in place; text for the guess is the record's name/title/description."""
    if isinstance(rec.get(key), list):
        text = " ".join(str(rec.get(k) or "") for k in ("title", "name", "description", "why_fa", "focus_fa", "summary"))
        rec[key] = canon_domains(rec[key], text)
    return rec
