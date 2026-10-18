# ایجنت «توسعه بازار برون مرزی هوشمند»
**Smart Cross-Border Market Development Agent** – Parsa International Group, Istanbul

ایجنتی که هر روز مناقصه‌ها و RFPهای بین‌المللی مرتبط با محصولات هوشمند شرکت را پیدا می‌کند و امکان شرکت در آن‌ها را بررسی می‌کند. برای هر فرصت، بسته‌ی اقدام آماده می‌کند: یا نامه‌ی شرکت مستقیم، یا ایمیل یافتن شریک تجاری همراه با پیش‌نویس تفاهم‌نامه. در پایان به شما خبر می‌دهد و هر RFP را تا نهایی شدن پیگیری می‌کند.

> English summary at the end of this file.

---

## فهرست
1. [چه کاری انجام می‌دهد](#۱-چه-کاری-انجام-میدهد)
2. [معماری و جریان کار](#۲-معماری-و-جریان-کار)
3. [ساختار پوشه‌ها](#۳-ساختار-پوشهها)
4. [راه‌اندازی آنلاین روی GitHub Actions](#۴-راهاندازی-آنلاین-روی-github-actions)
5. [اجرای محلی روی ویندوز](#۵-اجرای-محلی-روی-ویندوز)
6. [دستورها و پیگیری RFP تا نهایی شدن](#۶-دستورها-و-پیگیری-rfp-تا-نهایی-شدن)
7. [تنظیمات: حوزه‌ها، محصولات و منابع](#۷-تنظیمات-حوزهها-محصولات-و-منابع)
8. [خروجی‌ها](#۸-خروجیها)
9. [هزینه](#۹-هزینه)
10. [امنیت، حریم خصوصی و انطباق](#۱۰-امنیت-حریم-خصوصی-و-انطباق)
11. [عیب‌یابی](#۱۱-عیبیابی)
12. [نقشه‌ی راه](#۱۲-نقشهی-راه)
13. [English summary](#english-summary)

---

## ۱. چه کاری انجام می‌دهد

| مرحله | کار ایجنت | خروجی برای شما |
|---|---|---|
| استخراج | **بین‌المللی:** TED (اتحادیه اروپا)، بانک جهانی، Find a Tender (بریتانیا) · **داخلی:** سامانه ستاد (setadiran.ir)، فقط حوزه‌ی هوش مصنوعی | — |
| غربالگری | حذف موارد نامرتبط با کلیدواژه‌های حوزه‌های فعالیت و مهلت (حداقل ۷ روز باقی‌مانده) | فهرست فرصت‌های مرتبط در داشبورد |
| تحلیل (Claude) | سنجش تناسب با محصولات گیت‌هاب، استخراج الزامات و تصمیم درباره‌ی امکان شرکت، با این فرض که شرکت **هیچ سابقه‌ی اجرایی** در هوشمندسازی ندارد | خلاصه‌ی فارسی، الزامات، ملاحظات انطباق، گام‌های بعدی |
| شرکت مستقیم (`direct`) | نگارش نامه‌ی ابراز علاقه یا Cover Letter و چک‌لیست مدارک | پیش‌نویس در **Drafts وب‌میل** + فایل Word چک‌لیست |
| نیاز به شریک (`partner_required`) | جست‌وجوی ۳ تا ۵ شرکت مناسب در کشور هدف، نگارش ایمیل همکاری و تنظیم **تفاهم‌نامه‌ی همکاری در مناقصه (Teaming MoU)** | پیش‌نویس ایمیل در **Drafts وب‌میل** با پیوست MoU (Word) |
| غیرقابل‌انجام (`not_feasible`) | کنار گذاشتن مورد با ذکر دلیل | — |
| اعلان | پیام تلگرام و/یا ایمیل: «اسکن انجام شد – فلان نیاز در فلان کشور در انتظار شماست» | پیام روزانه |
| شرایط در یک نگاه | استخراج قیمت (برآورد یا قیمت پایه)، شرایط ضمانت‌نامه، شرایط رزومه، رفرنس و نمونه‌کار، و شرایط پذیرش شرکت‌های بین‌المللی | تب «شرایط شرکت در مناقصه در یک نگاه» |
| پیگیری | ثبت وضعیت هر RFP و یادآوری مهلت‌ها در ۱۴، ۷، ۳ و ۱ روز مانده | داشبورد فارسی |

### داشبورد: چهار صفحه
| صفحه | منبع | تب‌ها | به‌روزرسانی |
|---|---|---|---|
| **پروژه‌های هوش مصنوعی ایران** | سامانه ستاد – فقط فراخوان‌های حوزه‌ی هوش مصنوعی | فرصت‌ها · شرایط شرکت در مناقصه در یک نگاه | روزانه |
| **بازار بین‌المللی** | TED، بانک جهانی، Find a Tender | فرصت‌ها · شرایط در یک نگاه · **شرکای کشورهای ستاره‌دار** | روزانه (شرکا: هفتگی برای هر کشور) |
| **طراحی سایت و سئو** | درخواست‌های طراحی سایت و سئو از همه‌ی منابع داخلی و بین‌المللی، با کشور مبدأ | فرصت‌ها · شرایط در یک نگاه | روزانه |
| **رویدادهای هوش مصنوعی** | فهرست تحقیق‌شده‌ی اولیه + جست‌وجوی روزانه‌ی Claude | ایران · جهان · همه | روزانه |

- **شرایط در یک نگاه:** قیمت پیشنهادی یا برآورد، شرایط ضمانت‌نامه، شرایط رزومه، رفرنس و نمونه‌کار، و شرایط پذیرش شرکت‌های بین‌المللی.
- **بخش دولتی یا خصوصی:** برای همه‌ی RFPها مشخص است، مثل دولتی، شرکت دولتی/عمومی، سازمان بین‌المللی یا خصوصی دارای حقوق ویژه. در TED از نوع حقوقی خریدار و در ستاد از نام دستگاه استخراج می‌شود.
- **طراحی سایت:** برای مشتریان داخل ایران، پیشنهاد پیش‌فرض «طراحی سایت + سئو» است.
- **رویدادها:** هر رویداد شامل تاریخ (با لینک منبع)، حوزه، دلیل اهمیت و نحوه‌ی مشارکت است. اگر تاریخ رسمی اعلام نشده باشد، زمان معمول برگزاری نوشته می‌شود. وضعیت شرکت را با `python -m agent event <id> registered` ثبت کنید.

### کشورهای ستاره‌دار و شریک‌یابی
1. روی ☆ کنار نام کشور در صفحه‌ی بین‌المللی بزنید تا روش کار را ببینید. نام کشور را در `config.json` ← `starred_countries` اضافه کنید (در GitHub ویرایش مستقیم ممکن است) یا دستور `python -m agent star "Pakistan"` را اجرا کنید.
2. در اجرای بعدی، ایجنت برای هر کشور ستاره‌دار حدود ۶ شرکت فعال در حوزه‌های مشابه را پیدا می‌کند. منبع، وب‌سایت شرکت‌ها و صفحه‌ی عمومی LinkedIn آن‌هاست که در نتایج جست‌وجو آمده. ایجنت وارد LinkedIn نمی‌شود و صفحه‌های آن را جمع‌آوری خودکار نمی‌کند.
3. برای هر شرکت یک **ایمیل اختصاصی با موضوع** نوشته می‌شود و در **Drafts وب‌میل parsaint.group** ذخیره می‌شود. **آدرس گیرنده** فقط وقتی پر می‌شود که شرکت یک ایمیل عمومی کسب‌وکار (مثل info@ یا sales@) را روی سایت خودش منتشر کرده باشد. لینک صفحه‌ی منبع در تب «شرکا» آمده است. ایمیل شخصی افراد جمع‌آوری یا حدس زده نمی‌شود.
4. بعد از ارسال، وضعیت را ثبت کنید: `python -m agent partner <key> sent` (یا replied / meeting / mou / not_interested).

### سامانه ساتع
فیلترهای «پژوهشی»، «فناوری» و «فعال» در `config.json` ← `sources.sate` ثبت شده‌اند. جمع‌آورنده‌ی این سامانه پس از دریافت آدرس دقیق آن فعال می‌شود.

**ایجنت هیچ ایمیلی را ارسال نمی‌کند.** همه‌ی مکاتبات فقط به‌صورت پیش‌نویس در `parsaint.group/webmail` ذخیره می‌شوند و مطالعه، ویرایش و ارسال با خود شماست.

---

## ۲. معماری و جریان کار

```
 GitHub Actions (هر روز ۰۷:۳۰ استانبول)
        │
        ▼
 sources.py ──► TED API  │  World Bank API  │  UK Find a Tender (OCDS)  │  ستاد (setadiran.ir)
        │
        ▼
 screening.py   کلیدواژه + مهلت  ──►  store.py (وضعیت هر RFP)
        │
        ▼
 analyst.py  (Claude Opus 5.5)
   ├─ analyse()          تناسب، الزامات، direct / partner_required / not_feasible
   ├─ partner_package()  جست‌وجوی وب برای شریک + ایمیل + MoU
   └─ direct_package()   نامه‌ی ابراز علاقه + چک‌لیست
        │
        ├─► documents.py  فایل‌های Word (MoU، چک‌لیست) در outputs/
        ├─► mailbox.py    ذخیره‌ی پیش‌نویس در Drafts وب‌میل (IMAP)
        ├─► dashboard.py  داشبورد فارسی docs/index.html
        └─► notify.py     تلگرام / ایمیل
```

---

## ۳. ساختار پوشه‌ها

| مسیر | توضیح |
|---|---|
| `agent/sources.py` | جمع‌آورنده‌های مناقصه (یک تابع برای هر منبع) |
| `agent/screening.py` | غربالگری با کلیدواژه و مهلت |
| `agent/analyst.py` | تحلیل و نگارش با Claude (پرامپت‌ها و ساختار خروجی JSON) |
| `agent/portfolio.py` | پروفایل توانمندی شرکت از `products.json` و ریپازیتوری‌های گیت‌هاب |
| `agent/documents.py` | ساخت فایل‌های Word |
| `agent/mailbox.py` | ذخیره‌ی پیش‌نویس در وب‌میل از طریق IMAP |
| `agent/notify.py` | اعلان تلگرام و ایمیل |
| `agent/store.py` | وضعیت RFPها در `data/tenders.json` |
| `agent/dashboard.py` | داشبورد HTML فارسی |
| `agent/pipeline.py` | ترتیب اجرای روزانه |
| `config.json` | حوزه‌ها، کلیدواژه‌ها، منابع، سقف‌ها و مدل |
| `products.json` | خطوط محصول، میزان بلوغ و نیاز به بررسی مالکیت فکری |
| `.github/workflows/daily.yml` | زمان‌بندی روزانه روی GitHub |
| `run_daily.ps1` | اجرای روزانه روی ویندوز (جایگزین GitHub) |
| `.env.example` | فهرست متغیرهای محرمانه |

---

## ۴. راه‌اندازی آنلاین روی GitHub Actions

### گام ۱ – ریپازیتوری را خصوصی کنید (مهم)
Settings ← General ← Danger Zone ← **Change repository visibility ← Private**

در ریپازیتوری عمومی، ایجنت کار می‌کند ولی پیش‌نویس‌ها، MoUها، فهرست شرکا و داشبورد را **commit نمی‌کند**. وضعیت در کش خصوصی Actions نگه داشته می‌شود و پیش‌نویس‌ها همچنان به وب‌میل می‌روند، اما داشبورد در ریپازیتوری به‌روز نمی‌شود. حساب رایگان GitHub برای ریپازیتوری خصوصی ماهانه ۲۰۰۰ دقیقه Actions دارد. هر اجرای روزانه حدود ۵ تا ۱۵ دقیقه طول می‌کشد.

### گام ۲ – کلید Claude API
در [platform.claude.com](https://platform.claude.com) ← API Keys یک کلید بسازید و اعتبار حساب را شارژ کنید.

### گام ۳ – ربات تلگرام
1. در تلگرام به `@BotFather` پیام دهید ← `/newbot` ← نام ربات ← **توکن** را کپی کنید.
2. به ربات جدید یک پیام (مثلاً `سلام`) بدهید.
3. آدرس `https://api.telegram.org/bot<TOKEN>/getUpdates` را باز کنید و عدد `"chat":{"id": ...}` را بردارید. این همان **chat id** است.

### گام ۴ – Secrets
Settings ← Secrets and variables ← Actions ← **New repository secret**

| نام Secret | مقدار | الزامی؟ |
|---|---|---|
| `ANTHROPIC_API_KEY` | کلید گام ۲ | برای تحلیل و نگارش، بله |
| `IMAP_HOST` | `mail.parsaint.group` | برای ذخیره‌ی پیش‌نویس، بله |
| `IMAP_PORT` | `993` | اختیاری |
| `IMAP_USER` | `info@parsaint.group` | بله |
| `IMAP_PASSWORD` | رمز همین صندوق | بله |
| `TELEGRAM_BOT_TOKEN` | توکن گام ۳ | برای اعلان |
| `TELEGRAM_CHAT_ID` | chat id گام ۳ | برای اعلان |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `NOTIFY_EMAIL` | برای اعلان ایمیلی به صندوق خودتان | اختیاری |

در بخش **Variables** (نه Secrets) می‌توانید `DASHBOARD_URL` را برای نمایش لینک داشبورد در اعلان‌ها تعریف کنید.

### گام ۵ – اولین اجرا
تب **Actions** ← `daily-tender-scan` ← **Run workflow**. از این به بعد، هر روز ساعت ۰۷:۳۰ به وقت استانبول خودکار اجرا می‌شود.

### گام ۶ (اختیاری) – داشبورد آنلاین
داشبورد در `docs/index.html` ساخته می‌شود. در ریپازیتوری خصوصی می‌توانید آن را دانلود کنید یا از Code ← docs ← index.html ← Raw ذخیره و باز کنید. GitHub Pages برای ریپازیتوری خصوصی به حساب پولی نیاز دارد و برای ریپازیتوری عمومی توصیه نمی‌شود، چون اطلاعات تجاری را عمومی می‌کند.

---

## ۵. اجرای محلی روی ویندوز

```powershell
pip install -r requirements.txt
copy .env.example .env      # سپس .env را با Notepad پر کنید
python -m agent run --no-llm   # تست رایگان: فقط استخراج و غربالگری
python -m agent run            # اجرای کامل
```
برای اجرای خودکار روزانه: Task Scheduler ← Create Basic Task ← Daily ← Action: `powershell.exe -File "<مسیر>\run_daily.ps1"`. در این حالت کامپیوتر باید روشن باشد.

---

## ۶. دستورها و پیگیری RFP تا نهایی شدن

```bash
python -m agent run [--no-llm] [--no-mail] [--no-notify]   # اجرای روزانه
python -m agent list            # RFPهای فعال
python -m agent list --all      # همه، از جمله کنارگذاشته و منقضی
python -m agent status <ID> <وضعیت> "یادداشت"   # جلو بردن یک RFP
python -m agent redo <ID>       # تحلیل و پیش‌نویس دوباره
python -m agent dashboard       # ساخت دوباره‌ی داشبورد
```

**وضعیت‌ها:**

| کد | معنی | معمولاً بعد از |
|---|---|---|
| `new` | جدید، تحلیل نشده | استخراج |
| `analysed` | تحلیل شده | تحلیل Claude |
| `partner_search` | ایمیل شریک و MoU در Drafts | نیاز به شریک |
| `bid_prep` | نامه و چک‌لیست شرکت مستقیم آماده | امکان شرکت مستقیم |
| `mou_negotiation` | شریک پاسخ داده و MoU در حال مذاکره است | پاسخ شریک |
| `proposal_drafting` | نگارش پروپوزال فنی و مالی | امضای MoU |
| `submitted` | پیشنهاد ارسال شد | ارسال |
| `won` / `lost` | نتیجه | اعلام نتیجه |
| `skipped` / `expired` | کنار گذاشته شد / مهلت گذشت | — |

**همراهی تا نهایی شدن:** این پوشه را در Claude Code باز کنید و مثلاً بگویید «روی WB-OP00465889 کار کنیم». تحلیل، MoU و پیش‌نویس‌های آن مورد در `outputs/<ID>/` هستند و از آن‌ها برای نگارش پروپوزال فنی، پاسخ به پرسش‌های کارفرما و نهایی کردن MoU استفاده می‌شود.

---

## ۷. تنظیمات: حوزه‌ها، محصولات و منابع

- **`config.json` ← `domains`:** پنج دسته‌ی حوزه‌ی فعالیت، هر کدام با کلیدواژه‌های انگلیسی خودش:

  | دسته | نمونه کلیدواژه‌ها | محصولات مرتبط |
  |---|---|---|
  | `energy` انرژی | digital twin، predictive maintenance، refinery، oil and gas، energy management system، carbon management، smart grid | OGIM، FIDPS، IntelliLift، ApexAsset، دوقلوی دیجیتال فرایند، iEMS، توربین گازی، ترمینال مخازن |
  | `medical` پزشکی | clinical decision support، medical imaging، hospital information system، genomics، drug discovery | NeuroPredict-AI، سرطان مری، کیت‌های تشخیصی، کلان‌داده‌ی سلامت، فارماکوژنومیک، IPIND، LNP، CAR-T، HQCA |
  | `aviation` هوانوردی | airport operations، aircraft maintenance، aircraft engine monitoring، air traffic management | توربین گازی (پایش موتور)، ApexAsset، داشبوردهای نگهداری مبتنی بر وضعیت |
  | `nuclear` هسته‌ای | nuclear power plant، reactor monitoring، radiation monitoring | دوقلوی دیجیتال راکتور، نگهداری پیش‌بینانه‌ی هسته‌ای |
  | `urban` شهری | smart city، traffic management system، smart building، water distribution network، crisis management | بهینه‌سازی HVAC، iEMS، تصمیم‌یار بحران و لجستیک، بهینه‌سازی شبکه‌ی گاز |

- **`domestic_keywords`:** همان پنج دسته با کلیدواژه‌های فارسی برای جست‌وجو در ستاد.
- **`domestic_required_any`:** هر فراخوان داخلی باید در عنوانش حداقل یکی از واژه‌های فناوری (هوشمند، سامانه، نرم‌افزار، هوش مصنوعی، پایش و…) را داشته باشد. این قاعده تعمیرات ساختمان و خرید قطعه را حذف می‌کند.
- **`domestic_exclude_keywords`:** حذف مزایده، حراج، کالاهای مصرفی، مرمت و موارد مشابه.

  گروه `ai_cross_cutting` شامل کلیدواژه‌های عمومی هوش مصنوعی است که در همه‌ی دسته‌ها امتیاز می‌دهند. برای هوانوردی هنوز محصول اختصاصی وجود ندارد و فرصت‌ها بر اساس قابلیت‌های مشترک (نگهداری پیش‌بینانه، دوقلوی دیجیتال، پایش توربین) سنجیده می‌شوند.
- **`exclude_keywords`:** کلیدواژه‌هایی که آگهی را حذف می‌کنند، مثل نظامی، ساختمانی یا پذیرایی.
- **`screening`:** حداقل روز باقی‌مانده تا مهلت، حداقل امتیاز کلیدواژه، و سقف روزانه‌ی تحلیل و بسته‌ی شریک.
- **`products.json`:** خطوط محصول برگرفته از ریپازیتوری‌های گیت‌هاب، همراه با میزان بلوغ واقعی. با هر محصول جدید یک ردیف اضافه کنید. ریپازیتوری‌های جدیدی که در هیچ ردیفی نیستند در خروجی اجرا (`unmapped_repos`) گزارش می‌شوند.
- **`sources`:** روشن یا خاموش کردن هر منبع و تعداد روزهای بازنگری.

---

## ۸. خروجی‌ها

| مسیر | محتوا |
|---|---|
| `outputs/<ID>/analysis.json` | تحلیل کامل |
| `outputs/<ID>/partner_package.json` | شرکای پیشنهادی، متن ایمیل، بندهای MoU |
| `outputs/<ID>/MoU-draft.docx` | پیش‌نویس تفاهم‌نامه |
| `outputs/<ID>/checklist.docx` | چک‌لیست شرکت مستقیم |
| `outputs/<ID>/draft.eml` | نسخه‌ی پشتیبان پیش‌نویس ایمیل |
| `data/tenders.json` | وضعیت و تاریخچه‌ی همه‌ی RFPها |
| `docs/index.html` | داشبورد فارسی |
| Drafts وب‌میل | پیش‌نویس ایمیل‌ها، آماده‌ی ویرایش و ارسال |

---

## ۹. هزینه

- استخراج، غربالگری، داشبورد و GitHub Actions: **رایگان**.
- Claude Opus 5.5: حداکثر ۸ تحلیل و ۳ بسته‌ی شریک در روز. به‌طور تقریبی **۱ تا ۵ دلار در روز**، بسته به تعداد فرصت‌ها. سقف‌ها در `config.json` قابل تغییرند.
- برای تست رایگان از `--no-llm` استفاده کنید.

---

## ۱۰. امنیت، حریم خصوصی و انطباق

- **رمزها** فقط در GitHub Secrets یا فایل `.env` محلی نگه‌داری می‌شوند. `.env` در `.gitignore` است و هرگز commit نمی‌شود.
- **ارسال نکردن:** ایجنت فقط پیش‌نویس می‌سازد و هیچ ایمیلی ارسال نمی‌کند.
- **ریپازیتوری عمومی:** نتایج commit نمی‌شوند (گام ۱ بخش ۴).
- **صداقت:** ایجنت سابقه، گواهی، تعداد کارکنان یا پروژه‌ی جعلی نمی‌سازد و بلوغ محصولات را واقعی (نمونه‌ی اولیه، TRL 4–5) بیان می‌کند.
- **مالکیت فکری:** محصولات با `ip_check: true` در README گیت‌هاب‌شان «محصول اختصاصی یک کارفرمای مشخص» معرفی شده‌اند. پیش از ارائه در مناقصه‌ی خارجی، مالکیت حقوقی را روشن کنید. نام کارفرمایان در هیچ مکاتبه‌ای ذکر نمی‌شود.
- **تحریم و انطباق:** در هر تحلیل، ریسک‌های انطباق علامت زده می‌شوند، از جمله قواعد واجد شرایط بودن بانک جهانی، تحریم‌ها، کنترل صادرات و ثبت محلی. ایجنت هرگز پنهان‌کاری درباره‌ی مالکیت یا مبدأ را پیشنهاد نمی‌کند. **پیش از اولین ارسال با مشاور حقوقی مشورت کنید.**
- **داده‌ی اشخاص:** در جست‌وجوی شریک فقط اطلاعات عمومی شرکت‌ها (نام، وب‌سایت و ایمیل عمومی مثل info@) جمع می‌شود، نه اطلاعات شخصی افراد.

---

## ۱۱. عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| `ANTHROPIC_API_KEY not set` | Secret را اضافه کنید. تا آن زمان فقط استخراج انجام می‌شود. |
| `could not save webmail draft` | IMAP_HOST، رمز و پورت ۹۹۳ را بررسی کنید. نسخه‌ی پشتیبان در `outputs/<ID>/draft.eml` است. |
| پیش‌نویس در Drafts دیده نمی‌شود | در Roundcube پوشه‌ی Drafts را رفرش کنید. نام پوشه در `config.json` ← `mail` قابل تنظیم است. |
| اعلان تلگرام نمی‌آید | باید قبلاً به ربات پیام داده باشید. chat id را دوباره از getUpdates بخوانید. |
| موارد نامرتبط زیاد است | کلیدواژه‌ها را دقیق‌تر کنید یا `min_keyword_score` را بالا ببرید. |
| مورد مهمی جا افتاده | کلیدواژه‌ی آن را به حوزه‌ی مربوط اضافه کنید یا `lookback_days` را بیشتر کنید. |
| در ریپازیتوری فایلی ذخیره نمی‌شود | ریپازیتوری عمومی است. آن را Private کنید. |
| `Setad unreachable from this network` | سامانه ستاد ممکن است درخواست‌های سرورهای خارج از ایران (GitHub) را مسدود کند. در این صورت `run_daily.ps1` را روی کامپیوتری در ایران زمان‌بندی کنید تا بازار داخلی هم پوشش داده شود. |

---

## ۱۲. نقشه‌ی راه

- منابع بیشتر: UNGM (سازمان ملل)، ADB، AfDB، EBRD، IsDB، پورتال‌های کشورهای حوزه‌ی خلیج فارس، EKAP ترکیه، سامانه‌های مناقصات شرکت ملی نفت، گاز و پتروشیمی
- تحلیل هوشمند و پیش‌نویس فارسی برای فراخوان‌های داخلی
- دریافت و خلاصه‌سازی خودکار اسناد کامل مناقصه (PDF)
- پیش‌نویس پروپوزال فنی بر اساس الزامات استخراج‌شده
- پیگیری خودکار پاسخ شرکا در صندوق ورودی و پیشنهاد گام بعدی

---

## English summary

**What it does.** Every day the agent collects new tenders/RFPs from TED (EU), the World Bank and UK Find a Tender, screens them against five business categories (energy, medical, aviation, nuclear, urban), also lists Iranian domestic procurement notices from Setad (setadiran.ir) on a separate dashboard page, shows bid conditions at a glance (price, guarantees, references, acceptance of international firms), and uses Claude (Opus 5.5) to assess fit with the GitHub product portfolio and whether Parsa International Group, which has no prior contract references, can bid directly. If it can, the agent drafts an expression-of-interest letter and a bid checklist. If a local partner is needed, it researches 3–5 candidate partners in the buyer's country, drafts a teaming outreach email and a teaming MoU (Word), and saves the email as a draft in the parsaint.group webmail via IMAP. **It never sends email.** A Telegram/email notification summarises the day ("X need in country Y is waiting for you"), deadlines are reminded at 14/7/3/1 days, and every RFP is tracked through statuses until it is won or lost.

**Setup.** Make this repository private, add the secrets listed in section 4 (`ANTHROPIC_API_KEY`, `IMAP_*`, `TELEGRAM_*`), then trigger *Actions → daily-tender-scan → Run workflow*. The workflow runs daily at 07:30 Istanbul time. In a public repository, results are kept in the private Actions cache and not committed.

**Commands.** `python -m agent run | list | status <id> <status> | redo <id> | dashboard`.

**Compliance.** The agent states product maturity honestly, never invents references, flags IP-ownership checks and sanctions/eligibility risks in every analysis, and never suggests concealing ownership or origin. Seek legal advice before the first submission.
