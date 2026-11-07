import datetime
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Tahoma"
doc = Document()
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
for m in ("left_margin", "right_margin"): setattr(sec, m, Cm(1.3))
sec.top_margin = sec.bottom_margin = Cm(1.4)


def rtl(p):
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:bidi"); pPr.append(b); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def run(p, text, bold=False, size=10, color=None):
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(size); r.font.name = FONT
    rPr = r._r.get_or_add_rPr(); rf = rPr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rPr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), FONT)
    rt = OxmlElement("w:rtl"); rPr.append(rt)
    if color: r.font.color.rgb = RGBColor(*color)
    return r


def para(text, bold=False, size=10, color=None, space=4):
    p = doc.add_paragraph(); rtl(p); run(p, text, bold, size, color); p.paragraph_format.space_after = Pt(space); return p


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hexcolor); tcPr.append(s)


def table(headers, rows, widths, fills=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    tblPr = t._tbl.tblPr; bv = OxmlElement("w:bidiVisual"); tblPr.append(bv)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""; p = c.paragraphs[0]; rtl(p); run(p, h, True, 9, (255, 255, 255)); shade(c, "1F3A5F")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; p = cells[i].paragraphs[0]; rtl(p); run(p, str(v), False, 8.5)
            if fills and fills[ri].get(i): shade(cells[i], fills[ri][i])
    t.autofit = False
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    for i, w in enumerate(widths): t.columns[i].width = Cm(w)
    for row in t.rows:
        for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    return t


GREEN, YEL, RED, GREY = "D8EFD8", "FFF2CC", "F8D7D7", "E7E6E6"
today = datetime.date.today().isoformat()
para("گزارش یکجای ۲۰ محصول: بلوغ فناوری (TRL 4) و داده‌ی واقعی", True, 16, (31, 58, 95), 2)
para(f"تاریخ گزارش: {today} | مبنا: ممیزی مخازن GitHub، آزمایش‌های پوشه‌ی research/ در مخزن بازار، و فهرست داده‌ها (research/DATA_CATALOGUE.md)", False, 9, (90, 90, 90), 8)

para("۱) خلاصه‌ی اجرایی", True, 12)
for t in [
    "TRL 4 در این گزارش یعنی «اجزا در محیط آزمایشگاهی اعتبارسنجی شده‌اند»؛ معیار عملی: کد + تست خودکار + CI + سند TRL با شواهد. این ارزیابی رسمی TRL نیست.",
    "TRL 4 مستند و آزموده: ۱۱ از ۲۰ محصول (۹ محصول articles-*، IPIND، و محصول پتروشیمی `s_ps` که همین امروز اسکفلد شد). همه‌ی آن‌ها روی داده‌ی سینتتیک‌اند؛ TRL 5 برای هیچ‌کدام ادعا نمی‌شود.",
    "کد و تست دارند ولی سند TRL ندارند (TRL 4 اثبات‌نشده): ۷ محصول. بدون تست و بدون CI (TRL 4 ندارند): ApexAsset و دوقلوی هسته‌ای.",
    "داده‌ی واقعی: فقط ۵ محصول با اندازه‌گیری واقعی آزموده شده‌اند (ApexAsset، HQCA، StratGuard، IntelliLift، FIDPS)؛ ۳ محصول با داده‌ی محاسباتی یا بنچمارک استاندارد (QGrid، StretchWatch، Shot-Budget)؛ ۱۰ محصول به‌خاطر مسدود بودن پایگاه‌های داده آزموده نشده‌اند و ۲ محصول منبع عمومی ندارند.",
    "اعداد چکیده‌ها فقط برای ۸ محصول از آزمایش خودِ من آمده است. برای ۱۱ محصول دیگر چکیده هنوز اعداد قبلی ثبت‌شده در پایگاه داده (اجراهای خودتان) را دارد و باید قبل از ارسال دوباره اجرا شود؛ چکیده‌ی `s_ps` به [to be measured] برگشته است.",
]: para("• " + t, False, 9.5, None, 3)

rows = [
 # (id, venue, product, repo, trl, trl_note, real, real_note, abs_note)
 ("s_isie","IEEE ISIE 2027","ApexAsset AI","-ApexAsset-AI","نه (B)","۷۱ فایل کد، ۰ تست، بدون CI، بدون سند TRL","انجام شد","NASA IMS: ۴ خرابی یاتاقان؛ کران پایین RUL","بازنویسی با اعداد واقعی؛ اعداد شاخص‌اند"),
 ("s_iqim","IQIM 2027","HQCA (کشف دارو)","HQCA-Hybrid-Quantum-Classical-Drug-Discovery","اثبات‌نشده (C)","۲۴ فایل کد، ۳ تست، بدون CI/TRL","انجام شد","ChEMBL EGFR، ۳٬۸۸۴ ترکیب؛ پوشش ۰٫۸۹۶؛ Mondrian بدون سود","بازنویسی با اعداد واقعی"),
 ("s_eg","Energy Geoscience (SI)","StratGuard","articles-stratguard-facies","TRL 4 مستند (D)","۸ فایل کد، تست، CI، docs/TRL.md","انجام شد","SEG 2016 (۱۰ چاه) + FORCE 2020 (۸۱ چاه)؛ بدترین چاه ۰٫۵۹۹","بازنویسی؛ مجوز FORCE را بررسی کنید"),
 ("s_pet","Petroleum (KeAi)","IntelliLift","i-lift---AI-Powered-Artificial-Lift-Management-Dashboard","اثبات‌نشده (C)","۱۶۰ فایل کد، ۲۱ تست، ۲ CI، بدون سند TRL","انجام شد","Petrobras 3W v2: ۱٬۱۱۹ نمونه‌ی واقعی؛ نرخ هشدار کاذب ۰٫۱۴۷ (هدف ۰٫۱۰)","بازنویسی؛ نتیجه‌ی منفی"),
 ("s_iai","IAI2027","FIDPS","FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-","اثبات‌نشده (C)","۱۰۰ فایل کد، ۱ تست، بدون CI/TRL","انجام شد (جایگزین)","FORCE 2020، ۶۲ چاه؛ مرز گروه‌ها به‌جای داده‌ی آسیب سازند؛ PELT ۰٫۳۳ در برابر ۰٫۳۰","بازنویسی؛ داده‌ی آسیب واقعی ندارد"),
 ("s_iqicsa","IQICSA 2027","QGrid-Part","articles-qgrid-part","TRL 4 مستند (D)","۹ فایل کد، تست، CI، TRL.md","بنچمارک استاندارد","شبکه‌های IEEE 9 و 14 باس + پخش بار AC (pandapower)؛ QAOA از حریص بهتر نیست","بازنویسی"),
 ("s_icqe","ICQE 2027","StretchWatch","articles-stretchwatch-vqe","TRL 4 مستند (D)","۵ فایل کد، تست، CI، TRL.md","محاسباتی","PySCF FCI/CCSD(T) برای H2، LiH، BeH2، H2O؛ ۵ نقطه‌ی SCF مشکوک علامت‌گذاری شد","بازنویسی"),
 ("s_qip","QIP 2027 (پوستر)","Shot-Budget Lab","articles-qshot-lab","TRL 4 مستند (D)","۶ فایل کد، تست، CI، TRL.md","محاسباتی","هامیلتونی H2 و LiH (PySCF/OpenFermion)؛ shadows ≈۳× بدتر از یکنواخت","بازنویسی؛ نتیجه‌ی منفی"),
 ("s_icmhi","ICMHI 2027","IPIND","N---Barekat---IPIND---Intelligent-Platform-for-Integrated-Nanocarrier-Design","TRL 4 مستند (D)","۹۲ فایل کد، ۱۶ تست، CI، TRL_ASSESSMENT (TRL 4 اثبات، TRL 5 نه)","مسدود","داده‌ی LNP: منبع/لینک مجموعه را اعلام کنید","اعداد قبلی پایگاه داده"),
 ("s_aimh","AiMH 2027","LNP (ناقل ژن)","barekat-gen-therapy","اثبات‌نشده (C)","۱۱۰ فایل کد، ۹ تست، CI، بدون سند TRL","مسدود","داده‌ی LNP (LANTERN)؛ لینک تأییدشده پیدا نشد","اعداد قبلی پایگاه داده"),
 ("s_mimar","MIMAR2027","توربین گازی (دوقلو)","digital-twine-gas-turbine","اثبات‌نشده (C)","۱۶۷ فایل کد، ۲۰ تست، ۲ CI، بدون سند TRL","مسدود","UCI Gas Turbine CO/NOx","اعداد قبلی پایگاه داده"),
 ("s_jpse","J. Pipeline Sci. Eng.","ترمینال و مخزن","inno-terminals-tanks","اثبات‌نشده (C)","۷۶ فایل کد، ۴ تست، CI، بدون سند TRL","مسدود","EIA: موجودی هفتگی نفت خام آمریکا","اعداد قبلی پایگاه داده"),
 ("s_jimg","J. Imaging (MDPI) SI","ژنومیکس و PGx","barekat-Genomics","اثبات‌نشده (C)","۲۱۴ فایل کد، ۲۴ تست، بدون CI/TRL","مسدود","CPIC + gnomAD + 1000 Genomes (جدول فراوانی آلل‌ها)","اعداد قبلی پایگاه داده"),
 ("s_cmi","Current Med. Imaging SI","ExplainGuard","articles-explainguard-faithfulness","TRL 4 مستند (D)","۷ فایل کد، تست، CI، TRL.md","مسدود","PneumoniaMNIST (MedMNIST، Zenodo)","اعداد قبلی پایگاه داده"),
 ("s_front_nuc","Frontiers Nuclear AI","دوقلوی راکتور هسته‌ای","Digital-twin---nuc---reac","نه (B)","۵۶ فایل کد، ۰ تست، بدون CI/TRL","منبع عمومی ندارد","داده‌ی حادثه‌ی نیروگاه: منبع عمومی پیدا نشد","اعداد قبلی پایگاه داده"),
 ("s_ps","Petroleum Science (KeAi)","دوقلوی فرایند پتروشیمی","inno-Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System-","TRL 4 مستند (D)","اسکفلد امروز merge شد: ۶ تست، CI، TRL.md؛ فقط سینتتیک","منبع عمومی محدود","SRMG (فقط پژوهش دانشگاهی)؛ اجراهای قبلی حذف شد","برگشت به [to be measured]"),
 ("s_hydro","Hydrology (MDPI) SI","HydroGate","articles-hydrogate-streamflow","TRL 4 مستند (D)","۷ فایل کد، تست، CI، TRL.md","مسدود","CAMELS (NCAR)","اعداد قبلی پایگاه داده"),
 ("s_quantics","QUANTICS 2027","QRNG-Audit","articles-qrng-audit","TRL 4 مستند (D)","۶ فایل کد، تست، CI، TRL.md","مسدود","بیت‌های QRNG (IBM/ANU) + مرجع NIST STS","اعداد قبلی پایگاه داده"),
 ("s_mie","MIE 2027","ReadmitCal","articles-readmitcal-diabetes","TRL 4 مستند (D)","۶ فایل کد، تست، CI، TRL.md","مسدود","UCI Diabetes 130-US Hospitals","اعداد قبلی پایگاه داده"),
 ("s_npj","npj Digital Medicine","WearShift","articles-wearshift-har","TRL 4 مستند (D)","۷ فایل کد، تست، CI، TRL.md","مسدود","UCI HAR (۳۰ نفر)","اعداد قبلی پایگاه داده"),
]
fills = []
for r in rows:
    f = {}
    f[4] = GREEN if "مستند" in r[4] else (RED if r[4].startswith("نه") else YEL)
    f[6] = GREEN if r[6] == "انجام شد" else (YEL if r[6] in ("انجام شد (جایگزین)", "بنچمارک استاندارد", "محاسباتی", "منبع عمومی محدود") else (RED if r[6] == "منبع عمومی ندارد" else GREY))
    fills.append(f)

doc.add_paragraph()
para("۲) جدول ۲۰ محصول", True, 12)
para("رنگ‌ها: سبز = تأییدشده، زرد = ناقص یا غیرمستقیم، قرمز = ندارد، خاکستری = مسدود (در انتظار داده).", False, 8.5, (90, 90, 90))
table(["#", "مقصد (کد)", "محصول", "مخزن", "TRL 4 (وضعیت)", "شواهد مخزن", "داده‌ی واقعی", "جزئیات داده/نتیجه", "وضعیت چکیده"],
      [(i + 1, f"{r[1]} ({r[0]})", r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for i, r in enumerate(rows)],
      [0.7, 3.3, 2.6, 4.3, 2.0, 4.0, 2.0, 4.8, 2.6], [{**{k + 0: v for k, v in f.items()}} for f in [{4 + 0: f[4], 6: f[6]} for f in fills]])

doc.add_paragraph()
para("۳) محدودیت‌ها و هشدارها", True, 12)
for t in [
    "TRL 4 در همه‌ی موارد «روی داده‌ی سینتتیک» است. TRL 5 به اعتبارسنجی در محیط مرتبط (داده‌ی واقعی کارخانه/بالینی) نیاز دارد و برای هیچ‌کدام ادعا نمی‌شود.",
    "ادعای ثبت‌اختراع: حلقه‌ی مشترک لوله/کاتالیست/نسبت ماژول (Apadana) و توالی‌دهی ۱۹ گرید (AryaSasol) عمداً در مخزن عمومی پیاده نشده‌اند و منتظر نظر وکیل ثبت اختراع‌اند.",
    "آزمایش‌های داده‌ی واقعی در مخزن خصوصی `research/` (شاخه‌ی main مخزن بازار) هستند، نه در مخزن خود محصول؛ پس مخزن ApexAsset، HQCA، FIDPS و IntelliLift هنوز تست و TRL مستند خود را ندارند. پیشنهاد: پس از تأیید شما، بخش عمومی‌شده‌ی آن‌ها به مخزن محصول منتقل شود.",
    "مجوزها: FORCE 2020 و SRMG (فقط پژوهش دانشگاهی) پیش از انتشار باید بررسی شوند. هر مقاله فقط یک محصول دارد (قاعده‌ی «یک محصول، یک مقاله»).",
    "۹ مخزن `articles-*` هنوز public هستند و باید Private شوند.",
]: para("• " + t, False, 9.5, None, 3)

para("۴) کارهای لازم برای بستن شکاف‌ها (به ترتیب اولویت)", True, 12)
for t in [
    "دریافت داده‌ها (زیپ UCI HAR، Diabetes 130، Gas Turbine، EIA، CAMELS، MedMNIST، بیت‌های QRNG، جدول CPIC/gnomAD) یا باز کردن دسترسی شبکه؛ با رسیدن هر فایل، ماژول مربوطه اجرا و چکیده بازنویسی می‌شود.",
    "نوشتن سند TRL و CI برای ۷ محصول «کد + تست بدون سند» (HQCA، FIDPS، IntelliLift، توربین گازی، LNP، ژنومیکس، ترمینال).",
    "افزودن تست و CI برای ApexAsset و دوقلوی هسته‌ای تا حداقل به معیار TRL 4 برسند.",
    "تعریف محصول جدید برای فراخوان‌های «محصول ندارد» (APOGCE، NPIC، مجله‌ی هوانوردی AEI) با هم‌فکری.",
]: para("• " + t, False, 9.5, None, 3)

out = "outputs/PRODUCTS_TRL4_REAL_DATA_REPORT.docx"   # run from the repo root; PDF via: soffice --headless --convert-to pdf --outdir outputs <docx>
doc.save(out); print(out)
