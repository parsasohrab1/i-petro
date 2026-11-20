#!/usr/bin/env python3
"""
Build the per-article Word files (abstract + manuscript) and the article registry
for the iPetro platform "وضعیت ثبت" tab.

Sources (read-only, all from this repository):
  platform/abstracts_seed.json            20 venue abstracts + product/repo map
  outputs/manuscripts/manuscripts.json    16 structured manuscripts (blocks)
  outputs/manuscripts/MIMAR2027-...docx   manuscript for s_mimar (text extracted)
  outputs/manuscripts/artifacts/*.docx    4 repo-bundled manuscripts (article_drafts family)
  data/article_drafts.json                abstract + metadata for those 4
  platform/index.html                     ARTICLES_SEED venue rows (name/deadline/url/details)

Outputs:
  outputs/article_word_files/<venue>__<product>.docx   one Word file per article
  outputs/article_word_files/articles_registry_index.docx  registry index (all articles)
  outputs/article_word_files/ms_seed.json  compact manuscript map (embedded into platform/index.html)
  data/articles_export/article_registry.json + manifest.json  settings/article_registry doc
  copies of every .docx in /home/z/my-project/download/articles_word/

The script patches platform/index.html idempotently (/*MS-START*/ ... /*MS-END*/,
the "reg" sub-tab and the VIEWS["articles.reg"] view).

usage: python scripts/build_article_word_files.py
"""
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SEED = json.load(open(ROOT / "platform/abstracts_seed.json", encoding="utf-8"))
MSMAP = json.load(open(ROOT / "outputs/manuscripts/manuscripts.json", encoding="utf-8"))["map"]
DRAFTS = json.load(open(ROOT / "data/article_drafts.json", encoding="utf-8"))["drafts"]
INDEX_HTML = ROOT / "platform/index.html"
OUT = ROOT / "outputs/article_word_files"
DL = Path("/home/z/my-project/download/articles_word")
EXPORT = ROOT / "data/articles_export"
GH = "https://github.com/parsasohrab1/"
SUB_FAM = "outputs/manuscripts/"

# ---------------------------------------------------------------- venue rows from ARTICLES_SEED
def load_venues():
    html = INDEX_HTML.read_text(encoding="utf-8")
    start = html.index("const ARTICLES_SEED = [")
    end = html.index("];", start)
    block = html[start:end]
    venues = {}
    for m in re.finditer(r'\{id:"([^"]+)"', block):
        vid = m.group(1)
        # entry text runs to the next entry or the end of the block
        nxt = block.find('{id:"', m.end())
        entry = block[m.start():nxt if nxt != -1 else len(block)]
        def grab(key):
            mm = re.search(key + r':"((?:\\.|[^"\\])*)"', entry)
            return mm.group(1) if mm else ""
        venues[vid] = {"name": grab("name"), "deadline": grab("deadline"), "url": grab("url"),
                       "details": grab("details")}
    return venues

VENUES = load_venues()

# ---------------------------------------------------------------- registry rows
def docx_paragraphs(path):
    doc = Document(str(path))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

def blocks_from_paras(paras):
    """Plain paragraphs -> structured blocks; numbered/section lines become headings."""
    blocks = []
    for t in paras:
        if re.match(r"^(\d+\.\d*|\d+\s+[A-Z]|Abstract$|References$|Keywords$|Acknowledg)", t):
            blocks.append({"t": "h", "x": t})
        else:
            blocks.append({"t": "p", "x": t})
    return blocks

def count_words(blocks):
    n = 0
    for b in blocks:
        if b["t"] in ("p", "h", "title"):
            n += len(b["x"].split())
        elif b["t"] == "ul":
            n += sum(len(x.split()) for x in b["x"])
        elif b["t"] == "table":
            n += sum(len(str(c).split()) for r in b["rows"] for c in r)
    return n

rows = []
# 1) seed family: 20 venue abstracts, 16 manuscripts from manuscripts.json + s_mimar from docx
for vid, a in SEED["abstracts"].items():
    prod = SEED["products"][a["product"]]
    repo = GH + prod["repo"] + ("" if prod.get("new") else "/tree/" + SEED["branch"])
    v = VENUES.get(vid, {})
    ms_file, blocks = "", []
    if vid in MSMAP:
        ms_file = SUB_FAM + vid[2:] + "-manuscript.docx"        # s_eg -> eg-manuscript.docx
        blocks = MSMAP[vid]["blocks"]
    elif vid == "s_mimar":
        f = ROOT / SUB_FAM / "MIMAR2027-manuscript-gas-turbine-drift.docx"
        ms_file = SUB_FAM + f.name
        blocks = blocks_from_paras(docx_paragraphs(f))
    rows.append({
        "kind": "seed", "id": vid, "venue": v.get("name", ""), "deadline": v.get("deadline", ""),
        "url": v.get("url", ""), "title": a["title"], "product_key": a["product"],
        "product_name": prod["name"], "repo_url": repo, "abstract": a["abstract"],
        "keywords": a.get("keywords", []), "profile": SEED["profiles"][a["profile"]]["label"],
        "author": "Mohammad Parsa Sohrabi", "ms_file": ms_file, "ms_blocks": blocks,
        "status": "ms" if ms_file else "abs", "trl": "",
    })

# 2) repo-bundled drafts (data/article_drafts.json) with manuscripts in outputs/manuscripts/artifacts
for k, d in DRAFTS.items():
    f = ROOT / SUB_FAM / "artifacts" / f"{k}-manuscript.docx"
    rows.append({
        "kind": "artifact", "id": k, "venue": d.get("venue_name", ""), "deadline": "",
        "url": d.get("venue_url", ""), "title": d["abstract"]["title"], "product_key": d["product"],
        "product_name": d.get("product_full_name") or d["product"],
        "repo_url": GH + d["product"], "abstract": d["abstract"]["text"],
        "keywords": d["abstract"].get("keywords", []), "profile": "—",
        "author": d.get("submitting_team_member", "Parsa Babaei"),
        "ms_file": SUB_FAM + f"artifacts/{k}-manuscript.docx",
        "ms_blocks": blocks_from_paras(docx_paragraphs(f)),
        "status": "ms", "trl": str(d.get("trl", "")),
    })

# 3) applied conference/journal submissions (p_*): title recorded, no bundled text
for vid, v in VENUES.items():
    if not vid.startswith("p_"):
        continue
    m = re.search(r"مقاله‌ی ارسالی: ?([^«\n]+)", v.get("details", ""))
    rows.append({
        "kind": "paper", "id": vid, "venue": v.get("name", ""), "deadline": v.get("deadline", ""),
        "url": v.get("url", ""), "title": (m.group(1).strip() if m else ""),
        "product_key": "", "product_name": "—", "repo_url": "", "abstract": "", "keywords": [],
        "profile": "—", "author": "", "ms_file": "", "ms_blocks": [], "status": "abs", "trl": "",
    })

STATUS_FA = {"ms": "ثبت منواسکریپت", "abs": "ثبت خلاصه", "none": "بی‌اقدام"}

# ---------------------------------------------------------------- docx helpers
def set_style(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    rf = normal.element.get_or_add_rPr().get_or_add_rFonts()
    for attr in ("w:hAnsi", "w:cs"):
        rf.set(qn(attr), "Times New Roman")
    for name, size in (("Heading 1", 16), ("Heading 2", 13)):
        st = doc.styles[name]
        st.font.name = "Times New Roman"; st.font.size = Pt(size)
        st.font.bold = True; st.font.color.rgb = RGBColor(0, 0, 0)
        rf = st.element.get_or_add_rPr().get_or_add_rFonts()
        for attr in ("w:hAnsi", "w:cs"):
            rf.set(qn(attr), "Times New Roman")

def para(doc, text="", align=None, bold=False, italic=False, size=12, rtl=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if rtl:
        p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
    if text:
        r = p.add_run(text)
        r.bold = bold; r.italic = italic; r.font.size = Pt(size)
        if rtl:
            r._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
    return p

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)

def table_margins(table):
    mar = OxmlElement("w:tblCellMar")
    for side, w in (("top", 80), ("left", 120), ("bottom", 80), ("right", 120)):
        el = OxmlElement(f"w:{side}"); el.set(qn("w:w"), str(w)); el.set(qn("w:type"), "dxa")
        mar.append(el)
    table._tbl.tblPr.append(mar)

def row_flags(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    if header:
        trPr.append(OxmlElement("w:tblHeader"))

def kv_table(doc, pairs):
    """Two-column key/value sheet; Persian label column (RTL) + value column."""
    table = doc.add_table(rows=len(pairs), cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_margins(table)
    for i, (label, value) in enumerate(pairs):
        c0, c1 = table.rows[i].cells
        p0 = c0.paragraphs[0]; p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p0._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
        r0 = p0.add_run(label); r0.bold = True; r0._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
        shade(c0, "F5F7FA")
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(value if value else "—")
        if label == "وضعیت مقاله":
            p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p1._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
            r1._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
            r1.bold = True
        row_flags(table.rows[i])
    for w, col in ((2800, 0), (7800, 1)):
        for row in table.rows:
            row.cells[col].width = Pt(w / 20)
    return table

def add_page_number(doc):
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), r"PAGE \* arabic \* MERGEFORMAT")
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "1"
    r.append(t); fld.append(r)
    p._p.append(fld)

def ms_table(doc, head, data_rows):
    table = doc.add_table(rows=len(data_rows) + 1, cols=len(head))
    table.style = "Table Grid"
    table_margins(table)
    for j, h in enumerate(head):
        cell = table.rows[0].cells[j]
        cell.paragraphs[0].add_run(h).bold = True
        shade(cell, "F5F7FA")
    row_flags(table.rows[0], header=True)
    for i, r in enumerate(data_rows, start=1):
        for j, v in enumerate(r):
            table.rows[i].cells[j].paragraphs[0].add_run(str(v))
    for row in table.rows:
        row_flags(row)
    return table

def article_docx(row, fname):
    doc = Document()
    set_style(doc)
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Pt(72)
    sec.left_margin = Pt(85); sec.right_margin = Pt(71)
    add_page_number(doc)
    # title + author
    para(doc, row["title"], align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=4)
    if row["author"]:
        para(doc, row["author"] + "  ·  Parsa International Group, Istanbul, Türkiye  ·  oil.ms.sohrabi@gmail.com",
             align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=10, space_after=10)
    # registry sheet: the four requested values first
    ms_words = count_words(row["ms_blocks"]) if row["ms_blocks"] else 0
    files = ["فایل ورد این مقاله: " + fname]
    if row["ms_file"]:
        files.append("متن منواسکریپت از: " + row["ms_file"] + (f" (~{ms_words} کلمه)" if ms_words else ""))
    pairs = [
        ("نام مقاله", row["title"]),
        ("نام محصول", row["product_name"]),
        ("آدرس ریپو", row["repo_url"]),
        ("وضعیت مقاله", STATUS_FA[row["status"]]),
        ("مقصد (venue)", row["venue"]),
        ("مهلت", row["deadline"] or "—"),
        ("پروفایل چکیده", row["profile"]),
    ]
    if row.get("trl"):
        pairs.append(("TRL", row["trl"]))
    pairs.append(("فایل‌ها", "  ·  ".join(files) if files else "—"))
    kv_table(doc, pairs)
    para(doc, "", space_after=2)
    # abstract section
    doc.add_heading("خلاصه مقاله (Abstract)", level=1)
    if row["abstract"]:
        para(doc, row["abstract"], align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        if row["keywords"]:
            p = para(doc, "", space_after=0)
            r = p.add_run("Keywords: "); r.bold = True
            p.add_run("; ".join(row["keywords"]))
    else:
        para(doc, "متن خلاصه در ریپو ذخیره نشده است؛ فقط عنوان مقاله‌ی ارسالی ثبت شده است.", italic=True)
    # manuscript section
    doc.add_heading("منواسکریپت (Manuscript)", level=1)
    if row["ms_blocks"]:
        blocks = row["ms_blocks"]
        if blocks and blocks[0]["t"] == "title":
            blocks = blocks[1:]
        for b in blocks:
            if b["t"] == "h":
                doc.add_heading(b["x"], level=2)
            elif b["t"] == "p":
                para(doc, b["x"], align=WD_ALIGN_PARAGRAPH.JUSTIFY)
            elif b["t"] == "ul":
                for item in b["x"]:
                    para(doc, "• " + item, space_after=3)
            elif b["t"] == "table":
                ms_table(doc, b["head"], b["rows"])
                para(doc, "", space_after=2)
    else:
        para(doc, "منواسکریپت برای این مقاله هنوز تهیه نشده است؛ در وضعیت فعلی فقط خلاصه ثبت شده است.", italic=True)
    return doc

def index_docx(all_rows):
    doc = Document()
    set_style(doc)
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Pt(72)
    sec.left_margin = Pt(85); sec.right_margin = Pt(71)
    add_page_number(doc)
    doc.add_heading("فهرست مقالات و وضعیت ثبت — iPetro", level=1)
    n_ms = sum(1 for r in all_rows if r["status"] == "ms")
    n_abs = sum(1 for r in all_rows if r["status"] == "abs")
    para(doc, "این فایل چکیده و منواسکریپت هر محصول را از فایل‌های ریپو استخراج و در فایل‌های ورد جداگانه "
              "(پوشه‌ی outputs/article_word_files) گردآوری کرده است. برای هر مقاله چهار مقدار ثبت‌شده‌ی سامانه "
              "آمده است: آدرس ریپو، نام محصول، نام مقاله و وضعیت مقاله (ثبت خلاصه، ثبت منواسکریپت، بی‌اقدام). "
              f"جمع مقالات: {len(all_rows)}؛ ثبت منواسکریپت: {n_ms}؛ ثبت خلاصه: {n_abs}. همه‌ی ریپوها خصوصی‌اند (🔒).",
         align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    table = doc.add_table(rows=len(all_rows) + 1, cols=5)
    table.style = "Table Grid"
    table_margins(table)
    heads = ["نام مقاله", "نام محصول", "آدرس ریپو", "وضعیت مقاله", "مقصد"]
    for j, h in enumerate(heads):
        cell = table.rows[0].cells[j]
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
        r = p.add_run(h); r.bold = True; r._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
        shade(cell, "F5F7FA")
    row_flags(table.rows[0], header=True)
    for i, r in enumerate(all_rows, start=1):
        vals = [r["title"] or "—", r["product_name"], r["repo_url"] or "—", STATUS_FA[r["status"]], r["venue"] or r["id"]]
        for j, v in enumerate(vals):
            cell = table.rows[i].cells[j]
            p = cell.paragraphs[0]
            run = p.add_run(v)
            run.font.size = Pt(9)
            if j == 3:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
                run._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
                run.bold = True
            elif j == 2 and v != "—":
                run.font.size = Pt(8)
        row_flags(table.rows[i])
    for w, col in ((3300, 0), (2300, 1), (2300, 2), (1300, 3), (1300, 4)):
        for row in table.rows:
            row.cells[col].width = Pt(w / 20)
    return doc

# ---------------------------------------------------------------- build files
def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(s)).strip("-").lower() or "x"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DL.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    made = []
    for row in rows:
        if row["kind"] == "paper":
            continue   # no bundled abstract/manuscript text -> registry row only
        fname = f"{row['id']}__{slug(row['product_key'])}.docx"
        doc = article_docx(row, fname)
        doc.save(str(OUT / fname))
        shutil.copy2(OUT / fname, DL / fname)
        made.append(fname)
    idx = "articles_registry_index.docx"
    index_docx(rows).save(str(OUT / idx))
    shutil.copy2(OUT / idx, DL / idx)
    made.append(idx)
    # compact manuscript map for the platform
    ms_seed = {}
    for row in rows:
        if row["ms_file"] and row["status"] == "ms":
            ms_seed[row["id"]] = {"title": row["title"], "file": row["ms_file"],
                                  "words": count_words(row["ms_blocks"])}
    (OUT / "ms_seed.json").write_text(json.dumps(ms_seed, ensure_ascii=False), encoding="utf-8")
    # platform import snapshot (settings/article_registry)
    registry = {"updated": date.today().isoformat(), "count": len(rows), "list": [
        {"id": r["id"], "kind": r["kind"], "venue": r["venue"], "deadline": r["deadline"],
         "url": r["url"], "title": r["title"], "product_key": r["product_key"],
         "product_name": r["product_name"], "repo_url": r["repo_url"],
         "status_key": r["status"], "status_fa": STATUS_FA[r["status"]],
         "abstract_words": len(r["abstract"].split()) if r["abstract"] else 0,
         "manuscript_file": r["ms_file"], "manuscript_words": count_words(r["ms_blocks"]) if r["ms_blocks"] else 0}
        for r in rows]}
    (EXPORT / "article_registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"batches": [[{"collection": "settings", "doc_id": "article_registry",
                              "file_path": "data/articles_export/article_registry.json"}]]}
    (EXPORT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    patch_index(ms_seed)
    print(f"word files: {len(made)} (-> {OUT} and {DL})")
    print(f"registry rows: {len(rows)} (ms={sum(1 for r in rows if r['status']=='ms')}, "
          f"abs={sum(1 for r in rows if r['status']=='abs')})")
    print(f"ms_seed entries: {len(ms_seed)}; index.html patched: {'/*MS-START*/' in INDEX_HTML.read_text(encoding='utf-8')}")

# ---------------------------------------------------------------- index.html patch
def patch_index(ms_seed):
    html = INDEX_HTML.read_text(encoding="utf-8")
    ms_js = json.dumps(ms_seed, ensure_ascii=False, separators=(",", ":"))
    ms_line = f'/*MS-START*/const MS = {ms_js};/*MS-END*/'
    if "/*MS-START*/" in html:
        html = re.sub(r"/\*MS-START\*/.*?/\*MS-END\*/", lambda m: ms_line, html, flags=re.DOTALL)
    else:
        html = html.replace(";/*ABS-END*/", ";/*ABS-END*/\n" + ms_line, 1)
    sub_old = '["list","فهرست کامل"],["pipe"'
    sub_new = '["list","فهرست کامل"],["reg","وضعیت ثبت (ریپو · محصول · وضعیت)"],["pipe"'
    if '["reg","وضعیت ثبت' not in html:
        assert sub_old in html, "SUBS.articles anchor not found"
        html = html.replace(sub_old, sub_new, 1)
    view = '''
// ---- article registry: repo / product / title / registration status per article
// sources: ABS (embedded abstracts) + MS (repo manuscripts) + data/article_drafts.json + applied venues
VIEWS["articles.reg"] = () => {
  const main = artAll().map(a => {
    const abs = absOf(a.id), ms = MS[a.id];
    const mTitle = (a.details||"").match(/مقاله‌ی ارسالی: ?([^«\\n]+)/);
    const title = (ms&&ms.title) || (abs&&abs.title) || (mTitle&&mTitle[1].trim()) || "";
    const prod = abs ? absProd({product:abs.product}) : {name:"—",repo:"",new:false};
    const repo = prod.repo ? ABS_GH+prod.repo+(prod.new?"":"/tree/"+ABS.branch) : "";
    const st = ms ? "ms" : abs ? "abs" : artStatus(a)==="applied" ? "abs" : "none";
    return {a,title,prod,repo,st};
  });
  const extra = Object.entries(S.artDrafts||{}).filter(([k])=>!main.some(r=>r.a.id===k)).map(([k,d]) => {
    const ms = MS[k];
    return {a:{id:k,name:d.venue_name||k}, title:(ms&&ms.title)||(d.abstract&&d.abstract.title)||"",
      prod:{name:d.product_full_name||d.product||"—",repo:d.product||"",new:false},
      repo:d.product?ABS_GH+d.product:"", st:"ms"};
  });
  const rows = main.concat(extra);
  const L = {ms:["ثبت منواسکریپت","p-ok"],abs:["ثبت خلاصه","p-info"],none:["بی‌اقدام","p-mute"]};
  const cnt = k => rows.filter(r=>r.st===k).length;
  return `<p class="note">چهار مقدار ثبت‌شده برای هر مقاله: <b>آدرس ریپو</b>، <b>نام محصول</b>، <b>نام مقاله</b> و <b>وضعیت مقاله</b> (ثبت خلاصه، ثبت منواسکریپت، بی‌اقدام). منبع: چکیده‌های آماده‌ی سامانه، منواسکریپت‌های ریپو (outputs/manuscripts و data/article_drafts.json) و وضعیت ثبت مقصدها. فایل ورد جداگانه‌ی هر مقاله در <span class="mono">outputs/article_word_files</span> ریپو ساخته می‌شود (scripts/build_article_word_files.py). همه‌ی ریپوها خصوصی‌اند (🔒).</p>`+
   kpis([["ثبت منواسکریپت",faNum(cnt("ms"))],["ثبت خلاصه",faNum(cnt("abs"))],["بی‌اقدام",faNum(cnt("none"))],["جمع مقالات",faNum(rows.length)]])+
   table(["مقصد","نام مقاله","نام محصول","آدرس ریپو","وضعیت مقاله"],rows.map(r=>`<tr>${td("مقصد",esc(r.a.name),"t")}${td("نام مقاله",r.title?`<span dir="ltr">${esc(r.title)}</span>`:'<span class="meta">—</span>',"t")}${td("نام محصول",esc(r.prod.name))}${td("آدرس ریپو",r.repo?`${link(r.repo,"🔒 ریپو")}<br><span class="meta mono">${esc(r.repo.replace(ABS_GH,""))}</span>`:'<span class="meta">—</span>',"t")}${td("وضعیت",`<span class="pill ${L[r.st][1]}">${L[r.st][0]}</span>`)}</tr>`),"مقاله‌ای ثبت نشده است.");
};
'''
    anchor = '\nVIEWS["articles.pipe"]=()=>{'
    if 'VIEWS["articles.reg"]' not in html:
        assert anchor in html, "VIEWS anchor not found"
        html = html.replace(anchor, "\n" + view + anchor, 1)
    INDEX_HTML.write_text(html, encoding="utf-8")

if __name__ == "__main__":
    sys.exit(main())
