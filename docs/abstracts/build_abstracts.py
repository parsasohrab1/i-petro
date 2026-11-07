"""Build one Word file per journal/conference from platform/abstracts_seed.json.

usage: python docs/abstracts/build_abstracts.py VENUES_JSON [OUT_DIR]
VENUES_JSON is ARTICLES_SEED dumped as JSON (see README in this folder).
"""
import json, re, sys, pathlib
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn

ROOT = pathlib.Path(__file__).resolve().parents[2]
data = json.load(open(ROOT / "platform/abstracts_seed.json", encoding="utf-8"))
venues = {v["id"]: v for v in json.load(open(sys.argv[1], encoding="utf-8"))}
out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "outputs/abstracts"); out.mkdir(parents=True, exist_ok=True)
GH = "https://github.com/parsasohrab1/"

def font(run, size=11, bold=False, italic=False, color=None):
    run.font.name = "Times New Roman"; run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size); run.bold = bold; run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)

def para(doc, text="", size=11, bold=False, italic=False, align=None, after=6, color=None):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after)
    if align is not None: p.alignment = align
    if text: font(p.add_run(text), size, bold, italic, color)
    return p

def build(vid, v, a):
    pr = data["profiles"][a["profile"]]; prod = data["products"][a["product"]]
    n = len(re.findall(r"\S+", a["abstract"]))
    doc = Document(); s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    for m in ("left_margin", "right_margin"): setattr(s, m, Cm(2.5))
    s.top_margin = s.bottom_margin = Cm(2.5)
    para(doc, a["title"], 15, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
    para(doc, "[Author names]", 11, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    para(doc, "[Affiliation – e.g. Parsa International Group, Istanbul, Türkiye]  ·  [Corresponding author e-mail]", 10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
    para(doc, "Abstract", 12, True, after=4)
    para(doc, a["abstract"], 11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=8).paragraph_format.line_spacing = 1.15
    p = para(doc, "", after=4); font(p.add_run(pr["kw_label"] + ": "), 11, True); font(p.add_run("; ".join(a["keywords"])), 11, italic=True)
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)
    para(doc, "Submission sheet (internal – remove before submitting)", 12, True, color="B00020", after=6)
    rows = [("Venue", v["name"]), ("Type", {"journal": "Journal", "special": "Journal special issue", "conf": "Conference"}[v["type"]]),
            ("Deadline", (v.get("deadline") or "rolling") + ("  – " + v["dl_note"] if v.get("dl_note") else "")),
            ("Official page", v.get("url", "")), ("Abstract rule (" + pr["label"] + ")", f'{pr["rule"]}  Typical length {pr["min"]}–{pr["max"]} words; keywords {pr["kw"]}.'),
            ("Length of this abstract", f"{n} words (limit {pr['max']})"),
            ("Product", prod["name"]),
            ("Repository", GH + prod["repo"] + ("" if prod["new"] else "/tree/" + data["branch"])),
            ("Repository status", "New repository created for this article. It is PRIVATE: GitHub shows a 404 page to anyone who is not a collaborator (ask the owner for access; the repository is also hidden from search and from the repository list)." if prod["new"] else f'Existing product; content for the article is on branch "{data["branch"]}".'),
            ("To do before submitting", "Replace every [bracketed] placeholder with the team's own measured values; add author names; confirm the limits in the venue's author guidelines (they are typical values for the venue family, not copied from the call). Patent rule: do not disclose methods covered by the product's filed claims; a patent-attorney review is not required (owner's decision of 2026-11-07)." + ("  " + a["draft_note"] if a.get("draft_note") else ""))]
    t = doc.add_table(rows=0, cols=2); t.style = "Table Grid"
    for k, val in rows:
        c = t.add_row().cells; c[0].width = Cm(4.2); c[1].width = Cm(11.8)
        font(c[0].paragraphs[0].add_run(k), 10, True); font(c[1].paragraphs[0].add_run(val), 10)
    fn = out / f"{vid[2:]}_{re.sub(r'[^A-Za-z0-9]+', '-', v['name'].split(' – ')[0].split(' (')[0]).strip('-')[:40]}.docx"
    doc.save(fn); return fn

made = [build(k, venues[k], a) for k, a in data["abstracts"].items()]
print(len(made), "files in", out)
