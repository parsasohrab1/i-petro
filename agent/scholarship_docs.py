"""Word files for the scholarship track: opportunity list, owner's to-do list and the Derby application kit."""
from datetime import date

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import scholarships
from .config import ROOT

FONT = "Tahoma"
OUT = ROOT / "outputs"
REGIONS = [("uk", "بریتانیا"), ("europe", "اروپا"), ("other", "سایر نقاط جهان (بدون چین و روسیه)")]
LEVEL = {"master": "ارشد", "phd": "دکتری"}
# the only numbers given to institutions: verification codes and WhatsApp messages may come from them
CONTACT_MOBILE = "09123344295"
CONTACT_PHONE = "02188918530"
CONTACT_NOTE = f"شماره‌ی تماس برای همه‌ی ثبت‌نام‌ها: فقط موبایل ایران {CONTACT_MOBILE} و تلفن ایران {CONTACT_PHONE}؛ کد تأیید و پیام واتس‌اپ نهادها به همین شماره‌ها می‌رسد. در ایمیل به استادان و همه‌ی مکاتبات مدرک دکترای مدیریت کسب‌وکار یا DBA ذکر نشود."


class Doc:
    def __init__(self, landscape=False, rtl=True):
        self.d, self.rtl = Document(), rtl
        sec = self.d.sections[0]
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
        sec.left_margin = sec.right_margin = Cm(1.5)
        sec.top_margin = sec.bottom_margin = Cm(1.5)

    def _run(self, p, text, bold, size, color):
        r = p.add_run(text)
        r.bold, r.font.size, r.font.name = bold, Pt(size), FONT
        rPr = r._r.get_or_add_rPr()
        rf = rPr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rPr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), FONT)
        if self.rtl:
            rPr.append(OxmlElement("w:rtl"))
        if color:
            r.font.color.rgb = RGBColor(*color)

    def para(self, text, bold=False, size=10, color=None, space=4):
        p = self.d.add_paragraph()
        if self.rtl:
            p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        self._run(p, text, bold, size, color)
        p.paragraph_format.space_after = Pt(space)
        return p

    def h(self, text):
        return self.para(text, True, 12, (31, 58, 95), 6)

    def bullets(self, items):
        for t in items:
            self.para("• " + t, False, 10, None, 3)

    def table(self, headers, rows, widths, fills=None):
        t = self.d.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        if self.rtl:
            t._tbl.tblPr.append(OxmlElement("w:bidiVisual"))
        for i, h in enumerate(headers):
            c = t.rows[0].cells[i]
            c.text = ""
            self._cell(c, h, True, (255, 255, 255), "1F3A5F")
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                self._cell(cells[i], str(v), False, None, (fills or {}).get((ri, i)))
        t.autofit = False
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        t._tbl.tblPr.append(lay)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)

    def _cell(self, cell, text, bold, color, fill):
        p = cell.paragraphs[0]
        if self.rtl:
            p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        self._run(p, text, bold, 8.5, color)
        if fill:
            s = OxmlElement("w:shd")
            s.set(qn("w:val"), "clear")
            s.set(qn("w:color"), "auto")
            s.set(qn("w:fill"), fill)
            cell._tc.get_or_add_tcPr().append(s)

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / name
        self.d.save(path)
        return path


def _deadline_cell(s):
    d = scholarships.days_left(s)
    if d is None:
        return "مستمر / نامشخص", "FFF2CC"
    if d < 0:
        return f"{s['deadline']} (بسته شد)", "E7E6E6"
    return f"{s['deadline']} ({d} روز مانده)", ("F8D7D7" if d <= 14 else "D8EFD8")


AI_WORDS = ("هوش مصنوعی", "ai", "machine", "یادگیری", "informatics", "computer", "علوم کامپیوتر", "data", "رباتیک", "همه‌ی رشته")


def priority(s):
    """A/B/C = how realistic and fitting an application is now. A heuristic, not an admission probability."""
    if scholarships.is_closed(s):
        return "—", "بسته"
    left = scholarships.days_left(s)
    fit = any(w in (s.get("field", "") + s.get("name", "")).lower() for w in AI_WORDS)
    if "phd" not in s.get("levels", []):
        return ("B", "ارشد؛ برای هدف دکتری مناسب نیست") if fit else ("C", "ارشد و رشته‌ی دورتر")
    if left is not None and left < 10:
        return "C", "کمتر از ۱۰ روز؛ فقط اگر مدارک آماده است"
    if fit and (left is None or left >= 21):
        return "A", "رشته‌ی مرتبط + زمان کافی"
    return "B", "رشته یا زمان محدودکننده"


def _sorted(items):
    return sorted(items, key=lambda s: (s.get("id") != "derby_ai_phd", scholarships.is_closed(s), s.get("deadline") or "9999"))


def opportunities_doc(state):
    items = [s for s in state["scholarships"].values() if s.get("status") != "skipped"]
    d = Doc(landscape=True)
    d.para("فرصت‌های بورسیه‌ی فول‌فاند (ارشد و دکتری) – بدون چین و روسیه", True, 16, (31, 58, 95), 2)
    d.para(f"به‌روزرسانی: {date.today().isoformat()} | تعداد: {len(items)} فرصت | تأیید نهایی مهلت و شرایط همیشه از سایت رسمی هر برنامه "
           "(بسیاری از تاریخ‌ها از فهرست‌های ثانویه آمده‌اند و در ستون «توضیح مهلت» مشخص است).", False, 9, (90, 90, 90), 8)

    d.h("۱) خلاصه‌ی کشورها")
    by_country = {}
    for s in items:
        by_country.setdefault(s["country"], []).append(s)
    rows = []
    for c, lst in sorted(by_country.items(), key=lambda kv: -len(kv[1])):
        open_ = [s for s in lst if not scholarships.is_closed(s)]
        nxt = min((s["deadline"] for s in open_ if s.get("deadline")), default="-")
        rows.append((c, len(lst), len(open_), nxt, "؛ ".join(s["name"][:40] for s in lst[:3])))
    d.table(["کشور", "تعداد فرصت", "باز", "نزدیک‌ترین مهلت", "نمونه"], rows, [5, 2.2, 1.8, 3.2, 15])

    d.para("")
    d.h("۲) فرصت‌های فوری (۳۰ روز آینده)")
    soon = [s for s in _sorted(items) if (scholarships.days_left(s) is not None and 0 <= scholarships.days_left(s) <= 30)]
    d.bullets([f"{s['name']} – {s['country']} – {s['deadline']} ({scholarships.days_left(s)} روز) – {s['url']}" for s in soon]
              or ["موردی نیست."])

    n = 3
    for key, label in REGIONS:
        lst = _sorted([s for s in items if s.get("region") == key])
        if not lst:
            continue
        d.para("")
        d.h(f"{n}) {label}")
        n += 1
        rows, fills = [], {}
        for i, s in enumerate(lst):
            dl, color = _deadline_cell(s)
            fills[(i, 5)] = color
            if s["id"] == "derby_ai_phd":
                fills[(i, 0)] = "FFF2CC"
            rows.append((s["name"], f"{s['country']} – {s['uni']}", "، ".join(LEVEL.get(l, l) for l in s["levels"]),
                         s["field"], s["support"], dl, s.get("deadline_note", ""), s["url"], s.get("note", ""), "%s – %s" % priority(s)))
        d.table(["برنامه", "کشور و دانشگاه", "مقطع", "رشته", "پوشش مالی", "مهلت", "توضیح مهلت", "لینک رسمی", "یادداشت", "اولویت"],
                rows, [3.1, 3.0, 1.2, 3.0, 3.4, 2.3, 3.0, 3.4, 3.0, 1.6], fills)
    d.para("")
    d.h("منابع و محدودیت")
    d.bullets(["اطلاعات از جست‌وجوی وب در تاریخ بالا و فهرست تحقیق‌شده‌ی قبلی پلتفرم آمده است؛ سایت‌های مجمع‌کننده (aggregator) گاهی قدیمی‌اند.",
               "چین و روسیه طبق درخواست کنار گذاشته شده‌اند.",
               "واجد شرایط بودن شهروندان ایران (تحریم‌ها، ویزا، پرداخت هزینه‌ی درخواست) برای هر برنامه جداگانه باید بررسی شود."])
    return d.save("SCHOLARSHIPS_OPPORTUNITIES.docx")


def todo_doc(state):
    items = [s for s in state["scholarships"].values() if s.get("status") != "skipped" and not scholarships.is_closed(s)]
    urgent = [s for s in _sorted(items) if scholarships.days_left(s) is not None and scholarships.days_left(s) <= 45]
    d = Doc()
    d.para("کارهای لازم برای انجام توسط شما – بورسیه‌ی فول‌فاند", True, 16, (31, 58, 95), 2)
    d.para(f"تاریخ: {date.today().isoformat()} | این فایل هر روز با فهرست فرصت‌ها به‌روز می‌شود. کارهایی که هوش مصنوعی انجام می‌دهد در «بسته‌ی درخواست» آمده است.", False, 9, (90, 90, 90), 8)

    d.para(CONTACT_NOTE, True, 10, (180, 40, 30), 6)
    d.h("۱) اقدام فوری (مهلت ≤ ۴۵ روز)")
    d.table(["مهلت", "برنامه", "کار شما", "لینک"],
            [(s["deadline"], s["name"], "ثبت‌نام در پورتال رسمی، بارگذاری مدارک، ارسال نهایی؛ درخواست توصیه‌نامه همین هفته", s["url"]) for s in urgent]
            or [("-", "موردی نیست", "", "")], [2.4, 5.5, 6.5, 3.8])

    d.para("")
    d.h("۲) دربی – دکتری هوش مصنوعی فول‌فاند")
    d.bullets([
        "لینک یا عنوان دقیق آگهی Derby را به من بدهید؛ جست‌وجوی وب آگهی AI را تأیید نکرد (تنها آگهی فهرست‌شده غیر AI بود).",
        "اگر آگهی مشخص دارد: ایمیل پیوست «بسته‌ی درخواست Derby» را برای ‌supervisor یا Research Office ارسال کنید و بپرسید آیا شهریه‌ی بین‌المللی (۱۷٬۵۰۰ پوند) را پوشش می‌دهد.",
        "اطلاعات شخصی را در جاهای خالی [ ] بسته‌ی درخواست پر کنید (مدرک، معدل، مقاله‌ها)؛ آن‌ها را من حدس نمی‌زنم.",
    ])

    d.para("")
    d.h("۳) کارهایی که فقط خود شما می‌توانید انجام دهید")
    d.table(["#", "کار", "زمان‌بندی پیشنهادی", "یادداشت"], [
        (1, "آزمون زبان IELTS Academic (یا معادل پذیرفته‌شده؛ دانشگاه‌های بریتانیا اغلب ۶٫۵ تا ۷)", "ثبت‌نام این هفته", "زمان‌های آزمون زودتر پر می‌شود"),
        (2, "ریز نمرات و مدرک رسمی کارشناسی/ارشد به همراه ترجمه‌ی رسمی انگلیسی", "تا ۲ هفته", ""),
        (3, "۲ تا ۳ توصیه‌نامه از استادان یا مدیران (متن درخواست را من آماده کرده‌ام)", "تا ۳ هفته", "مهلت ELLIS برای توصیه‌نامه ۲۵ نوامبر ۲۰۲۶"),
        (4, "اسکن پاسپورت و عکس", "همین هفته", ""),
        (5, "ایجاد حساب در پورتال هر برنامه، پرداخت هزینه‌ی درخواست (اگر دارد) و ارسال نهایی", "قبل از مهلت", "پرداخت بین‌المللی از ایران ممکن است مشکل داشته باشد"),
        (6, "بررسی ویزا/تحریم و واجد شرایط بودن شهروند ایران برای هر برنامه", "قبل از درخواست", "ELLE/MSCA: قانون تحرک ۱۲ ماه"),
        (7, "تماس با ۲ تا ۳ استاد در دانشگاه‌های هدف (ایمیل آماده است)", "هفته‌ی آینده", "پاسخ استاد برای بورس‌های پروژه‌محور حیاتی است"),
        (8, "تأیید مشخصات قراردادی و بیمه، و مشاوره با وکیل ثبت اختراع در مورد محصولات ثبت‌نشده", "قبل از انتشار پروپوزال", "ادعاهای ثبت اختراع را در پروپوزال عمومی افشا نکنید"),
    ], [0.8, 8.5, 3.6, 5.3])
    d.para("")
    d.h("۴) کارهایی که من (هوش مصنوعی) انجام می‌دهم")
    d.bullets(["به‌روزرسانی روزانه‌ی فهرست فرصت‌ها و مهلت‌ها (فایل Word «فرصت‌های بورسیه»).",
               "پیش‌نویس انگیزه‌نامه، طرح پژوهشی، ایمیل به استاد، درخواست توصیه‌نامه و ساختار رزومه (بسته‌ی درخواست Derby؛ برای برنامه‌های دیگر به درخواست شما).",
               "هر پیش‌نویس پس از پر شدن [ ]ها توسط شما نهایی می‌شود."])
    return d.save("SCHOLARSHIP_OWNER_TODO.docx")


def derby_kit_doc():
    """English application drafts. Personal facts are left as [ ] placeholders on purpose."""
    d = Doc(rtl=False)
    d.para("University of Derby – PhD in Artificial Intelligence: application kit", True, 16, (31, 58, 95), 2)
    d.para(f"Draft prepared {date.today().isoformat()}. Fill every [bracket] with your real details before use. Nothing in this kit "
           "should claim results that have not been measured on real data.", False, 9, (90, 90, 90), 8)

    d.h("1. Email to the project supervisor / Research Office")
    d.para("Subject: Enquiry about the funded PhD studentship in Artificial Intelligence – [project title]\n\n"
           "Dear [Professor / Dr. surname],\n\n"
           "I am writing about the fully funded PhD studentship in [project title / area] at the University of Derby. I develop AI products "
           "at Parsa International Group (Istanbul), where I build machine-learning systems for industrial settings "
           "(oil and gas, health, aviation, nuclear and quantum computing). My background is [degree, university, year]. "
           "I am particularly interested in [one specific aspect of the project] because [one sentence linking it to your own work].\n\n"
           "Before applying, could you confirm: (1) whether the studentship is open to international applicants and whether the stipend "
           "(currently around £20,780 per year) is accompanied by payment of the overseas tuition fee; (2) the application deadline and start date; "
           "(3) the language and prior-experience requirements.\n\n"
           "I attach my CV and a short research outline and would be glad to discuss the project at your convenience.\n\n"
           f"Kind regards,\n[Name]\n{CONTACT_MOBILE} / {CONTACT_PHONE} / [email / ORCID]")

    d.h("2. Statement of purpose (draft, ~500 words)")
    d.para("I want to pursue a PhD in artificial intelligence because the hardest problems I meet in industry are not model-accuracy problems but "
           "trust problems: whether a model is correct under a distribution shift, whether its uncertainty is calibrated, and whether an engineer "
           "can act on its output. At Parsa International Group I have built [N] prototype systems for [domains], most at technology readiness level 4 "
           "on synthetic or public benchmark data. Working on them taught me where today's methods are weak: [1-2 concrete lessons, e.g. false-alarm "
           "rates above target on real well data; conformal intervals that do not improve a downstream decision].\n\n"
           "My academic training is [degree, thesis topic, supervisor]. [Publications / submitted papers: list only what is real.] "
           "I am drawn to the University of Derby's work on [group / centre / theme from the advert] because [specific reason]. "
           "I would contribute [skills: time-series ML, uncertainty quantification, digital twins, deployment].\n\n"
           "My proposed contribution is [project aim in one sentence]. In the first year I will [literature + baseline]; in the second [method]; in the third "
           "[validation on real data and write-up]. After the PhD I intend to [return to industry research / found a spin-out / academic career].")

    d.h("3. Research outline (one page; adapt to the advertised project)")
    d.bullets(["Title: [project title]",
               "Problem and motivation: [2-3 sentences; cite 2 recent papers you have actually read]",
               "Research questions: RQ1 [..] RQ2 [..] RQ3 [..]",
               "Methods: [learning method, uncertainty quantification, evaluation protocol on real data]",
               "Data: [public datasets and access route; state licence limits]",
               "Work plan: Year 1 [..] Year 2 [..] Year 3 [..]; expected outputs: [2-3 papers, one open-source tool]",
               "Risks and mitigation: data access, compute, generalisation"])

    d.h("4. Request to referees")
    d.para("Dear [Prof. / Dr. surname],\n\nI am applying for fully funded PhD positions in artificial intelligence, including one at the University of Derby (deadline [date]). "
           "As you know my work on [shared project / course], would you be willing to write a reference? I can send my CV, the research outline and the "
           "portal link; the reference is due by [date − 5 days]. Thank you for considering this.\n\nBest regards,\n[Name]")

    d.h("5. Academic CV structure")
    d.bullets(["Contact, ORCID, links", "Education (degree, university, GPA with scale, thesis title)",
               "Research and industry experience (3-4 bullets each, outcome first, only measured results)",
               "Publications and preprints (only real ones; mark 'under review')", "Projects and open-source work",
               "Skills (Python, PyTorch, time-series, UQ, MLOps)", "Languages (IELTS score and date)", "Referees (name, title, email)"])

    d.h("6. Application checklist")
    d.bullets(["Passport copy and photo", "Transcripts and certificates with certified English translations", "IELTS / equivalent report",
               "CV, statement, research outline", "2-3 references submitted through the portal", "Funding confirmation (stipend + overseas fee)",
               "Visa/ATAS check for the intended field"])
    return d.save("DERBY_AI_PHD_APPLICATION_KIT.docx")


def admission_plan_doc(state):
    """Why admission chances are low and what raises them. Scores are a transparent heuristic, not a probability."""
    d = Doc()
    d.para("برنامه‌ی ارتقای شانس پذیرش دکتری (بورسیه‌ی فول‌فاند)", True, 16, (31, 58, 95), 2)
    d.para(f"تاریخ: {date.today().isoformat()} | مبنا: ممیزی ۶۵ مخزن، کاتالوگ داده‌ی واقعی و چکیده‌های مقالات در همین مخزن. "
           "احتمال واقعی پذیرش را هیچ‌کس نمی‌تواند به درصد دقیق بگوید (به رقبا و تصمیم استاد بستگی دارد)؛ "
           "اینجا «شاخص آمادگی ۰ تا ۱۰۰» با معیارهای شفاف می‌دهم که با اقدام‌های زیر واقعاً بالا می‌رود.", False, 9, (90, 90, 90), 8)

    d.h("۱) چرا شانس پایین است؟ (بر پایه‌ی شواهد)")
    d.bullets([
        "کمیسیون‌های دکتری «سابقه‌ی پژوهشی تأییدشده» را می‌سنجند: مقاله‌ی داوری‌شده، پایان‌نامه، توصیه‌نامه‌ی استاد و تناسب با پروژه‌ی همان استاد. تعداد محصول در بازار یا داشبورد جای آن را نمی‌گیرد.",
        "مقاله‌ی «ثبت‌شده/در دست ثبت» تا پذیرش یا انتشار (حتی preprint قابل‌ارجاع) در رزومه ارزش پژوهشی ندارد. فقط موارد پذیرفته‌شده یا منتشرشده را «Published/Accepted» بنویسید.",
        "پراکندگی: نفت، سلامت، کوانتوم، هوانوردی و هسته‌ای در یک رزومه پیام «بدون پرسش پژوهشی مشخص» می‌دهد. استاد دنبال دانشجویی با یک خط پژوهشی روشن است.",
        "کیفیت شواهد: طبق ممیزی، ۱۰ مخزن بدون کد، ۹ مخزن بدون تست و فقط ۱۵ از ۶۵ مخزن سند TRL دارند؛ اغلب نتایج روی داده‌ی سینتتیک و TRL 4 است و فقط ۵ محصول با داده‌ی واقعی اندازه‌گیری شده است.",
        "بورس‌های فول‌فاند پروژه‌محور هستند: بدون ایمیل و پاسخ استاد، حتی رزومه‌ی قوی هم دیده نمی‌شود. تاکنون تماسی با استاد ثبت نشده است.",
        "تعداد و زمان درخواست‌ها: چند مهلت بسیار نزدیک (ELLIS و ETH) است و توصیه‌نامه‌های دانشگاهی هنوز آماده نیست.",
    ])

    d.para("")
    d.h("۲) شاخص آمادگی (۰ تا ۱۰۰) – وضع فعلی و هدف پس از اجرای برنامه")
    rows = [
        ("مقالات پذیرفته/منتشرشده و preprint قابل‌ارجاع", 25, 6, 15, "۱ تا ۲ مقاله‌ی کامل روی محصولات پرچم‌دار + arXiv"),
        ("تمرکز پژوهشی و روایت واحد", 20, 6, 16, "یک تز واحد (بخش ۳) و ۳ محصول پرچم‌دار به‌جای ۲۰ محصول"),
        ("کیفیت و تکرارپذیری شواهد", 15, 7, 12, "ریپوی تکرارپذیر، Zenodo DOI، داده‌ی واقعی، گزارش نتایج منفی"),
        ("تناسب و ارتباط با استاد راهنما", 15, 2, 11, "۱۰ تا ۱۵ ایمیل هدفمند؛ جدول پیگیری"),
        ("توصیه‌نامه‌ی دانشگاهی", 10, 3, 8, "۲ استاد + ۱ مدیر صنعتی"),
        ("پایه‌ی تحصیلی و زبان (معدل، IELTS)", 10, 5, 8, "داده‌ی شما لازم است؛ IELTS ثبت شود"),
        ("استراتژی درخواست (تعداد، زمان‌بندی)", 5, 2, 5, "فهرست اولویت A/B در فایل فرصت‌ها"),
    ]
    d.table(["معیار", "وزن", "فعلی (برآورد)", "هدف", "اقدام"],
            [(r[0], r[1], r[2], r[3], r[4]) for r in rows] + [("جمع", 100, sum(r[2] for r in rows), sum(r[3] for r in rows), "")],
            [6.0, 1.2, 2.2, 1.6, 6.8])
    d.para("نمره‌ی «فعلی» برای معیارهای نامشخص (معدل، توصیه‌نامه، مقالات پذیرفته) فرض محافظه‌کارانه است؛ اگر سابقه‌ی بهتری دارید مدرکش را بدهید تا اصلاح شود.", False, 8.5, (90, 90, 90))

    d.para("")
    d.h("۳) روایت واحد برای همه‌ی درخواست‌ها")
    d.para("تز پیشنهادی: «عدم قطعیت کالیبره و ارزیابی صادقانه‌ی یادگیری ماشین (و یادگیری ماشین کوانتومی) در تصمیم‌های ایمنی‌محور صنعتی و سلامت، تحت تغییر توزیع».", True, 10)
    d.para("چرا این روایت با سبد شما سازگار است (همه از نتایج همین مخزن):", False, 10)
    d.table(["محصول پرچم‌دار", "داده‌ی واقعی", "یافته‌ی قابل‌دفاع", "نقش در روایت"], [
        ("StratGuard (تشخیص رخساره‌ی چاه)", "SEG 2016 (۱۰ چاه) + FORCE 2020 (۸۱ چاه)", "پوشش conformal در بدترین چاه ۰٫۵۹۹؛ شکست پوشش تحت تغییر توزیع", "اثبات اصلی: عدم قطعیت و leave-one-well-out"),
        ("IntelliLift (هشدار چاه نفت)", "Petrobras 3W v2، ۱٬۱۱۹ نمونه‌ی واقعی", "نرخ هشدار کاذب ۰٫۱۴۷ در برابر هدف ۰٫۱۰", "نتیجه‌ی منفی صادقانه؛ ارزیابی تصمیم‌محور"),
        ("HQCA (کشف دارو)", "ChEMBL EGFR، ۳٬۸۸۴ ترکیب", "پوشش ۰٫۸۹۶؛ Mondrian سود نداشت", "پل به سلامت؛ conformal در دارو"),
        ("QGrid / Shot-Budget (کوانتوم)", "IEEE 9/14 باس؛ هامیلتونی H2/LiH", "QAOA از حریص بهتر نیست؛ shadows حدود ۳ برابر بدتر از یکنواخت", "ارزیابی منصفانه‌ی ادعاهای کوانتومی"),
    ], [4.2, 4.0, 5.2, 4.4])
    d.para("بقیه‌ی محصولات در رزومه به یک بند «Industrial prototypes» خلاصه شوند، نه بیست ردیف.", False, 9.5)

    d.para("")
    d.h("۴) برنامه‌ی ۶ هفته‌ای")
    d.table(["هفته", "اقدام", "مسئول"], [
        ("۱ (تا ۱ نوامبر)", "ثبت IELTS؛ ارسال درخواست توصیه‌نامه (متن آماده است)؛ ELLIS اگر مدارک آماده است؛ نام و ایمیل ۱۰ استاد هدف را در جدول پیگیری بگذارید", "شما + من (پیش‌نویس)"),
        ("۲", "نوشتن پروپوزال ۲ صفحه‌ای بر پایه‌ی تز بالا؛ تماس با ۲ استاد دربی (Dr Alaa AlZoubi و Dr Asad Abdi، طبق فهرست دانشگاه؛ تأیید شود)", "من پیش‌نویس؛ شما ارسال"),
        ("۳ تا ۴", "تبدیل StratGuard به مقاله‌ی کامل (۸ تا ۱۰ صفحه) با پروتکل leave-one-well-out، کد و داده‌ی تکرارپذیر؛ ثبت Zenodo DOI", "من (متن و تست)؛ شما تأیید مجوز FORCE"),
        ("۵", "انتشار preprint (با رعایت سیاست مجله و قاعده‌ی ثبت اختراع)؛ به‌روزرسانی رزومه: Published / Under review / In preparation جدا باشد", "شما + وکیل ثبت اختراع"),
        ("۶", "ارسال درخواست‌های اولویت A؛ پیگیری ایمیل‌ها", "شما"),
    ], [2.6, 10.0, 4.0])

    d.para("")
    d.h("۵) خط قرمزها برای حفظ اعتبار")
    d.bullets(["هیچ مقاله‌ی ثبت‌نشده، رتبه‌ی دانشگاه یا همکاری ساختگی در رزومه ننویسید؛ کمیسیون‌ها در Google Scholar و ORCID بررسی می‌کنند.",
               "نتایج منفی را مخفی نکنید: «ارزیابی صادقانه» نقطه‌ی قوت این روایت است.",
               "ادعاهای ثبت اختراع (حلقه‌ی Apadana، توالی‌دهی AryaSasol) را در پروپوزال و ایمیل‌ها فاش نکنید."])
    return d.save("ADMISSION_STRENGTH_PLAN.docx")


SKILLS = [  # (skill, evidence in this repository, level)
    ("Python scientific stack (NumPy, pandas, SciPy)", "همه‌ی ماژول‌های research/s_* (۸ ماژول با تست)", "اثبات‌شده"),
    ("Supervised ML – gradient boosting (scikit-learn HistGradientBoosting)", "StratGuard، HQCA (research/s_eg_stratguard، s_iqim_hqca)", "اثبات‌شده"),
    ("Uncertainty quantification – split / Mondrian conformal prediction", "StratGuard: پوشش ۰٫۸۸۹ روی ۸۱ چاه FORCE؛ HQCA: ۳٬۸۸۴ ترکیب ChEMBL", "اثبات‌شده"),
    ("Evaluation under distribution shift (leave-wells-out، worst-group coverage)", "StratGuard: بدترین چاه ۰٫۵۹۹، ۱۹ چاه زیر ۰٫۸۵", "اثبات‌شده"),
    ("Sequence decoding with domain constraints (Viterbi / transition grammar)", "StratGuard: ۷۲۶ تخطی گرامر به صفر", "اثبات‌شده"),
    ("Change-point detection and signal processing (ruptures/PELT, SciPy)", "FIDPS روی FORCE 2020 (۶۲ چاه)", "اثبات‌شده"),
    ("Prognostics – remaining useful life with isotonic calibration", "ApexAsset روی NASA IMS (۴ خرابی یاتاقان)", "اثبات‌شده"),
    ("Industrial anomaly / alarm design (false-alarm vs recall trade-off)", "IntelliLift روی Petrobras 3W v2 (۱٬۱۱۹ نمونه)", "اثبات‌شده"),
    ("Cheminformatics (RDKit, scaffold splits)", "HQCA: تقسیم بر پایه‌ی scaffold", "اثبات‌شده"),
    ("Quantum chemistry and quantum algorithms (PySCF, OpenFermion, VQE/QAOA, classical shadows)", "StretchWatch، Shot-Budget Lab، QGrid؛ نتایج منفی سنجیده‌شده", "اثبات‌شده (محاسباتی)"),
    ("Power-systems optimisation (pandapower AC power flow, IEEE 9/14 bus)", "QGrid-Part", "اثبات‌شده"),
    ("Software engineering for research (unit tests, CI, reproducible repos, TRL documentation)", "۱۵ مخزن با سند TRL؛ مثلاً i-drill ۸۸ تست و ۱۱ CI", "اثبات‌شده"),
    ("Productising AI (digital twins, dashboards, ERP integration)", "۶۵ مخزن و داشبورد هوشمند؛ بسیاری فقط TRL 4 و سینتتیک", "کاربردی (نمونه‌ی اولیه)"),
    ("Scientific writing and abstracts for venues", "۲۰ چکیده در outputs/abstracts؛ پذیرش هنوز مشخص نیست", "در جریان"),
]
LEARN = [
    "Deep learning با PyTorch روی یک مسئله‌ی همین سبد (مثلاً چاه‌نگاری) و مقایسه با baseline درختی",
    "روش‌های عدم قطعیت تکمیلی: Bayesian deep ensembles، conformal تحت تغییر توزیع (weighted/adaptive)",
    "علیت و تصمیم‌گیری تحت عدم قطعیت (cost-sensitive decision theory)",
    "MLOps: ردیابی آزمایش (MLflow)، داده‌ی نسخه‌دار (DVC)، Docker برای تکرارپذیری",
    "نگارش علمی: LaTeX، arXiv، ORCID، Google Scholar",
]


def skills_doc():
    """Skills section for CV / SOP, grounded only in what this repository can prove."""
    d = Doc()
    d.para("مهارت‌های هوش مصنوعی – بر پایه‌ی شواهد مخزن برای رزومه و انگیزه‌نامه", True, 16, (31, 58, 95), 2)
    d.para(f"تاریخ: {date.today().isoformat()} | هر مهارت فقط با شواهدی که در همین مخزن (کد، تست، نتیجه‌ی اندازه‌گیری‌شده) وجود دارد آمده است. "
           "رزومه‌ی شخصی شما (سال‌ها، مدارک، مقالات پذیرفته‌شده) در اختیار من نیست؛ آن بخش‌ها با [ ] خالی مانده است.", False, 9, (90, 90, 90), 8)
    d.h("۱) جدول مهارت و شواهد")
    d.table(["مهارت", "شاهد", "سطح"], SKILLS, [7.0, 8.0, 3.0],
            {(i, 2): ("D8EFD8" if s[2].startswith("اثبات") else "FFF2CC") for i, s in enumerate(SKILLS)})
    d.para("")
    d.h("۲) برنامه‌ی توسعه‌ی مهارت (۶ تا ۸ هفته؛ نه ادعا در رزومه تا انجام نشده)")
    d.bullets(LEARN)

    en = Doc(rtl=False)
    en.para("Technical Skills (CV-ready, English)", True, 14, (31, 58, 95), 4)
    en.para("Research focus: calibrated uncertainty and honest evaluation of machine learning (including quantum ML) for safety-critical industrial and health decisions.", True, 10)
    for h, items in [
        ("Machine learning and uncertainty", ["Gradient-boosted models (scikit-learn); split and Mondrian conformal prediction; group-wise (leave-wells-out) evaluation under distribution shift; worst-group coverage analysis",
                                              "Sequence decoding with domain grammars (Viterbi); change-point detection (PELT); isotonic calibration for remaining-useful-life estimates"]),
        ("Domain applications (public real-data studies)", ["Well-log facies classification on SEG 2016 (10 wells) and FORCE 2020 (81 wells); alarm design on Petrobras 3W v2 (1,119 real instances); bearing prognostics on NASA IMS; EGFR bioactivity modelling on ChEMBL (3,884 compounds)"]),
        ("Quantum computing for science", ["PySCF/OpenFermion Hamiltonians, VQE, QAOA and classical-shadow measurement; benchmark studies reporting negative results against classical baselines"]),
        ("Engineering practice", ["Python, NumPy/pandas/SciPy; unit tests, CI and reproducible repositories; technology-readiness (TRL) documentation; dashboards and digital-twin prototypes"]),
        ("Languages and tools", ["[Languages: Persian, English (IELTS [score, date]), Turkish [level]]", "[Add only tools you have used in a project]"]),
    ]:
        en.para(h, True, 10, None, 2)
        for it in items:
            en.para("• " + it, False, 10, None, 2)
    en.para("")
    en.para("Statement bullets for the SOP", True, 11, (31, 58, 95), 3)
    for b in ["I evaluate models the way deployment will: held-out wells, not random splits. On 81 FORCE wells, average conformal coverage met the 0.90 target (0.889) but the worst well reached only 0.599, which is why I study per-group guarantees.",
              "I report negative results. On Petrobras 3W the false-alarm rate was 0.147 against a 0.10 target, and quantum shot-allocation methods did not beat uniform allocation in my benchmarks.",
              "I build reproducible systems: tested code, CI and documented readiness levels, so that findings can be re-run by others."]:
        en.para("• " + b, False, 10, None, 3)
    en.save("AI_SKILLS_PROFILE_EN.docx")
    return d.save("AI_SKILLS_PROFILE.docx")


def proposals_doc():
    """Supervisor shortlist, email drafts and proposal text per university (English); source: proposals_seed.json."""
    import json
    data = json.loads((ROOT / "proposals_seed.json").read_text(encoding="utf-8"))
    d = Doc(rtl=False)
    d.para("PhD proposals, supervisor shortlists and email drafts", True, 16, (31, 58, 95), 2)
    d.para(f"Prepared {date.today().isoformat()}. Supervisors come from official staff pages and job ads; confirm their interest and addresses yourself. "
           "Emails are saved as drafts in Gmail (recipient left blank). Proposals are drafts: no result of the proposed work is claimed.", False, 9, (90, 90, 90), 8)
    for sid, v in data.items():
        d.h(v["university"])
        d.para("Note on format: " + v["format_note"], False, 9, (90, 90, 90))
        d.para("Supervisors to approach", True, 10)
        for s in v["supervisors"]:
            d.para(f"- {s['name']}, {s['role']} ({s['area']}) {s.get('url', '')}", False, 9.5, None, 2)
        for e in v["emails"]:
            d.para("Email to " + e["to_name"], True, 10)
            d.para("Subject: " + e["subject"], False, 9.5, None, 2)
            for chunk in e["body"].split("\n\n"):
                d.para(chunk, False, 9.5, None, 4)
        d.para("Proposal", True, 10)
        for chunk in v["proposal"].split("\n\n"):
            d.para(chunk, False, 9.5, None, 4)
        d.d.add_page_break()
    return d.save("SCHOLARSHIP_PROPOSALS_AND_EMAILS.docx")


def build_all(state):
    return [opportunities_doc(state), todo_doc(state), derby_kit_doc(), admission_plan_doc(state), skills_doc(), proposals_doc()]
