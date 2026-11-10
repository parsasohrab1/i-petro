#!/usr/bin/env python3
"""Generate one professional investor pitch deck (PPTX) per investor-facing product.

Evidence policy: only repo-audited facts, measured results from research/ (with dataset
sources), and cited public market reports. No invented traction or customers.
Output: outputs/pitch_decks/<slug>.pptx
"""
import re
import sys
from datetime import date
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product_data import all_outreach_products  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "pitch_decks"

NAVY = RGBColor(0x0F, 0x2A, 0x43)
TEAL = RGBColor(0x0F, 0xA3, 0xA3)
LIGHT = RGBColor(0xF5, 0xF7, 0xFA)
GREY = RGBColor(0x5A, 0x6B, 0x7B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xE8, 0xA1, 0x3D)
FONT = "Calibri"

SW, SH = Inches(13.333), Inches(7.5)


def _slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, x, y, w, h, color, line=False):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    if not line:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def _text(slide, x, y, w, h, runs, size=18, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    """runs: str or list of (text, dict-overrides) paragraphs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [(runs, {})]
    for i, (txt, ov) in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ov.get("align", align)
        p.line_spacing = ov.get("spacing", spacing)
        if ov.get("space_before"):
            p.space_before = Pt(ov["space_before"])
        r = p.add_run()
        r.text = txt
        f = r.font
        f.name = ov.get("font", FONT)
        f.size = Pt(ov.get("size", size))
        f.bold = ov.get("bold", bold)
        f.color.rgb = ov.get("color", color)
        f.italic = ov.get("italic", False)
    return tb


def _footer(slide, n, total):
    _text(slide, Inches(0.55), Inches(7.08), Inches(9), Inches(0.3),
          [("Parsa International Group  ·  parsaint.group  ·  info@parsaint.group", {"size": 9, "color": GREY})])
    _text(slide, Inches(12.3), Inches(7.08), Inches(0.7), Inches(0.3),
          [(f"{n} / {total}", {"size": 9, "color": GREY, "align": PP_ALIGN.RIGHT})])


def cover(prs, p):
    s = _slide(prs)
    _rect(s, 0, 0, SW, SH, NAVY)
    _rect(s, 0, Inches(4.72), Inches(1.6), Inches(0.09), TEAL)
    _text(s, Inches(0.55), Inches(0.5), Inches(9), Inches(0.5),
          [("PARSA INTERNATIONAL GROUP  ·  AI PRODUCTS PORTFOLIO", {"size": 14, "color": TEAL, "bold": True})])
    _text(s, Inches(0.55), Inches(2.0), Inches(12.2), Inches(2.2),
          [(p["title"], {"size": 40, "bold": True, "color": WHITE, "spacing": 1.05})])
    _text(s, Inches(0.55), Inches(3.6), Inches(12.0), Inches(1.0),
          [(p["desc"], {"size": 16, "color": RGBColor(0xC9, 0xD6, 0xE2), "spacing": 1.15})])
    _text(s, Inches(0.55), Inches(5.0), Inches(11.5), Inches(0.9),
          [("Technology readiness: " + p["trl_label"], {"size": 15, "color": ORANGE, "bold": True}),
           (f"Investor pitch deck  ·  {date.today().isoformat()}", {"size": 12, "color": RGBColor(0x9F, 0xB2, 0xC4), "space_before": 6})])
    _text(s, Inches(0.55), Inches(6.6), Inches(11), Inches(0.6),
          [("Narges Farahani  ·  AI Sector  ·  Istanbul, Türkiye  ·  info@parsaint.group  ·  parsaint.group",
            {"size": 12, "color": RGBColor(0xC9, 0xD6, 0xE2)})])
    return s


def problem(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("The problem & the opportunity", {"size": 26, "bold": True, "color": WHITE})])
    mkt = p["market"]
    _text(s, Inches(0.55), Inches(1.5), Inches(12.2), Inches(0.8),
          [("Industrial and healthcare operators in emerging markets lack affordable specialist software; decisions still depend on scarce experts.",
            {"size": 16, "color": NAVY, "bold": True, "spacing": 1.2})])
    y = Inches(2.55)
    for m in mkt:
        _rect(s, Inches(0.55), y, Inches(0.09), Inches(1.05), TEAL)
        _text(s, Inches(0.85), y, Inches(11.8), Inches(1.05),
              [(m, {"size": 15, "color": GREY, "spacing": 1.15})])
        y += Inches(1.3)
    _footer(s, n, total)
    return s


def solution(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("The product", {"size": 26, "bold": True, "color": WHITE})])
    _text(s, Inches(0.55), Inches(1.45), Inches(12.2), Inches(1.1),
          [(p["desc"], {"size": 16, "color": NAVY, "spacing": 1.2})])
    cards = [
        ("What it does", p["algorithms"] or "AI analytics over operational data"),
        ("Delivery", f'{p["frontend"]} · deployable on-premise or cloud'),
        ("Client context", p["client"] or "Developed inside the company product portfolio"),
    ]
    x = Inches(0.55)
    for t, v in cards:
        _rect(s, x, Inches(2.8), Inches(3.95), Inches(2.5), LIGHT)
        _rect(s, x, Inches(2.8), Inches(3.95), Inches(0.07), TEAL)
        _text(s, x + Inches(0.25), Inches(3.0), Inches(3.45), Inches(0.5), [(t, {"size": 14, "bold": True, "color": TEAL})])
        _text(s, x + Inches(0.25), Inches(3.5), Inches(3.45), Inches(1.7), [(v[:260], {"size": 12.5, "color": NAVY, "spacing": 1.15})])
        x += Inches(4.15)
    _rect(s, Inches(0.55), Inches(5.7), Inches(12.2), Inches(0.8), LIGHT)
    _text(s, Inches(0.8), Inches(5.82), Inches(11.7), Inches(0.6),
          [("One unique product per investor: this product is exclusively presented to you as the matched match of your focus areas.",
            {"size": 12.5, "color": GREY, "italic": True})])
    _footer(s, n, total)
    return s


def tech(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("Technology & architecture", {"size": 26, "bold": True, "color": WHITE})])
    rows = [
        ("Core algorithms", p["algorithms"] or "Machine learning over operational time-series"),
        ("Backend", " · ".join(p["tech"]) if isinstance(p["tech"], list) else str(p["tech"])),
        ("Frontend", p["frontend"]),
        ("Deployment", "Docker / on-premise / cloud - runs next to the plant data, no process-interruption integration required"),
        ("Integration", "OPC-UA / MQTT / REST to SCADA, historians and lab systems"),
    ]
    y = Inches(1.6)
    for k, v in rows:
        _rect(s, Inches(0.55), y, Inches(2.9), Inches(0.85), LIGHT)
        _text(s, Inches(0.75), y + Inches(0.18), Inches(2.6), Inches(0.5), [(k, {"size": 13, "bold": True, "color": NAVY})])
        _text(s, Inches(3.75), y + Inches(0.14), Inches(9.0), Inches(0.75), [(v, {"size": 13.5, "color": GREY})])
        y += Inches(1.02)
    _footer(s, n, total)
    return s


def validation(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("Validation & technology readiness", {"size": 26, "bold": True, "color": WHITE})])
    _text(s, Inches(0.55), Inches(1.35), Inches(12.2), Inches(0.6),
          [("Maturity: " + p["trl_label"], {"size": 16, "bold": True, "color": ORANGE})])
    y = Inches(2.1)
    for ev in p["evidence"]:
        _rect(s, Inches(0.55), y, Inches(0.09), Inches(1.0), TEAL)
        _text(s, Inches(0.85), y + Inches(0.02), Inches(2.7), Inches(1.0),
              [(ev["k"], {"size": 13, "bold": True, "color": NAVY})])
        _text(s, Inches(3.75), y, Inches(9.0), Inches(1.0),
              [(ev["v"], {"size": 13.5, "color": GREY, "spacing": 1.12})])
        y += Inches(1.12)
    _rect(s, Inches(0.55), Inches(6.1), Inches(12.2), Inches(0.7), LIGHT)
    _text(s, Inches(0.8), Inches(6.2), Inches(11.7), Inches(0.5),
          [("TRL definitions follow the standard scale: TRL 5 = component validation in a relevant environment; the next milestone is validation on customer operational data (TRL 6).",
            {"size": 11.5, "color": GREY, "italic": True})])
    _footer(s, n, total)
    return s


def market(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("Market & why now", {"size": 26, "bold": True, "color": WHITE})])
    figs = p["market"]
    x = Inches(0.55)
    w = Inches(3.95)
    for i, m in enumerate(figs[:3]):
        num, _, src = m.partition(" - ")
        head = num.split(":")[0] if ":" in num else num
        _rect(s, x, Inches(1.7), w, Inches(3.2), LIGHT)
        _rect(s, x, Inches(1.7), w, Inches(0.07), ORANGE)
        _text(s, x + Inches(0.25), Inches(1.95), w - Inches(0.5), Inches(1.6),
              [(head, {"size": 17, "bold": True, "color": NAVY, "spacing": 1.1})])
        _text(s, x + Inches(0.25), Inches(3.6), w - Inches(0.5), Inches(1.2),
              [("Source: " + (src or "public market report"), {"size": 11, "color": GREY})])
        x += Inches(4.15)
    _text(s, Inches(0.55), Inches(5.35), Inches(12.2), Inches(1.1),
          [("Why now: cheap edge hardware plus mature ML makes specialist-level analytics deployable at scale in emerging markets - exactly where our products run.",
            {"size": 15, "color": NAVY, "bold": True, "spacing": 1.2})])
    _footer(s, n, total)
    return s


def roadmap(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, Inches(1.15), NAVY)
    _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.7),
          [("Roadmap & the ask", {"size": 26, "bold": True, "color": WHITE})])
    steps = [
        ("Now", "Validated prototype (TRL 4-5); product exclusively matched to your focus"),
        ("Pilot (3-6 months)", "Validate on your operational data on one site; measure agreed KPIs together"),
        ("TRL 6-7", "Field-proven deployment at the pilot site; hardening and scale-out package"),
        ("Scale", "Commercial rollout with you as pilot partner and/or investor"),
    ]
    y = Inches(1.6)
    for t, v in steps:
        _rect(s, Inches(0.55), y, Inches(2.9), Inches(0.85), LIGHT)
        _text(s, Inches(0.75), y + Inches(0.18), Inches(2.6), Inches(0.5), [(t, {"size": 13, "bold": True, "color": TEAL})])
        _text(s, Inches(3.75), y + Inches(0.14), Inches(9.0), Inches(0.75), [(v, {"size": 13.5, "color": GREY})])
        y += Inches(1.02)
    _rect(s, Inches(0.55), Inches(5.9), Inches(12.2), Inches(0.9), NAVY)
    _text(s, Inches(0.85), Inches(6.08), Inches(11.6), Inches(0.6),
          [("The ask: pilot partner(s) and seed-stage funding to take this product through real-data validation.",
            {"size": 14.5, "bold": True, "color": WHITE})])
    _footer(s, n, total)
    return s


def contact(prs, p, n, total):
    s = _slide(prs)
    _rect(s, 0, 0, SW, SH, NAVY)
    _rect(s, 0, Inches(3.4), Inches(1.6), Inches(0.09), TEAL)
    _text(s, Inches(0.55), Inches(2.2), Inches(12), Inches(1.0),
          [("Let's talk", {"size": 40, "bold": True, "color": WHITE})])
    _text(s, Inches(0.55), Inches(3.7), Inches(12), Inches(1.6),
          [("Narges Farahani - AI Sector", {"size": 16, "color": WHITE, "bold": True}),
           ("Parsa International Group - Istanbul, Türkiye", {"size": 14, "color": RGBColor(0xC9, 0xD6, 0xE2), "space_before": 4}),
           ("info@parsaint.group  ·  parsaint.group", {"size": 14, "color": TEAL, "bold": True, "space_before": 4}),
           ("This deck is confidential and shared for evaluation of a potential pilot or investment discussion.",
            {"size": 11, "color": RGBColor(0x9F, 0xB2, 0xC4), "space_before": 10, "italic": True})])
    return s


def build(p, total=8):
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    cover(prs, p)
    problem(prs, p, 2, total)
    solution(prs, p, 3, total)
    tech(prs, p, 4, total)
    validation(prs, p, 5, total)
    market(prs, p, 6, total)
    roadmap(prs, p, 7, total)
    contact(prs, p, 8, total)
    return prs


def slugfile(slug):
    return re.sub(r"[^A-Za-z0-9]+", "-", slug).strip("-")[:80] + ".pptx"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prods, _ = all_outreach_products()
    made = []
    for p in prods:
        prs = build(p)
        f = OUT / slugfile(p["slug"])
        prs.save(str(f))
        made.append((p["slug"], f.name, f.stat().st_size))
    print(f"Generated {len(made)} decks in {OUT}")
    for slug, name, size in made:
        print(f"  {name}  ({size//1024} KB)  <- {slug[:60]}")


if __name__ == "__main__":
    main()
