# گزارش جامع محصولات (ممیزی مخازن GitHub) – 2026-10-24

> مبنا: ساختار فایل‌ها، تست‌ها، CI و اسناد TRL در هر مخزن (فقط شواهد مخزن؛ بدون اجرای محصولات). این گزارش «ارزیابی رسمی TRL» نیست؛ TRL باید با شواهد (تست، داده، محیط اعتبارسنجی) تأیید شود. مخزن‌های private (`hamrazsho.ir`) و مخزن پروفایل بررسی نشدند.

## ۱) خلاصه
| دسته | تعریف | تعداد |
|---|---|---|
| A | **فقط مستند/README و فاقد کد** | 10 |
| B | دارای کد ولی **بدون هیچ تست** | 9 |
| C | کد + تست، **بدون سند TRL** (TRL ثبت‌نشده) | 31 |
| D | کد + تست + **سند TRL** | 15 |
| | جمع مخازن بررسی‌شده | 65 |

### پاسخ به پرسش‌ها
1. **آیا محصولی هست که TRL آن ۴ نباشد؟** بله. فقط 15 مخزن سند TRL دارند و از آن‌ها ۴ تا ۶ ادعا شده (نک. جدول D). **19 مخزن (A و B) با معیار مهندسی (کد + تست خودکار) به TRL ۴ نمی‌رسند** و **31 مخزن (C) ممکن است ≥۴ باشند ولی سند و معیار خروج ندارند**، پس TRL ۴ آن‌ها اثبات‌نشده است.
2. **آیا محصولی فقط README دارد و فاقد کد است؟** بله، **10 مخزن** (دسته A؛ بیشترشان SRS/README بلند ولی صفر خط کد).
3. **آیا محصولی با داده واقعی تست نشده؟** بله، تقریباً همه. تست با داده واقعی را من فقط برای ۸ محصول انجام داده‌ام (ستون «داده واقعی»؛ کدها در مخزن خصوصی `research/` هستند، نه در مخزن خود محصول). برای ۴ محصول دیگر README ادعای داده واقعی یا برنامه‌ی آن را دارد ولی من بررسی نکرده‌ام. برای باقی (بیش از ۴۰ مخزن) شواهدی از آزمون با داده واقعی نیست و README یا فقط داده synthetic/sample/mock ذکر می‌کند یا اصلاً داده‌ای ذکر نمی‌کند.

## A) فقط مستند (بدون کد)
| مخزن | فایل کد | حجم کد (KB) | تست | CI | TRL مستند | داده واقعی |
|---|---|---|---|---|---|---|
| parsasohrab1/-Khalij-Apadana-Reformer-Methanol-Loop-Digital-Twin-System- | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/Gas-supply-and-demand-optimization-software-system | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/inno---inteligent-ref---park-naft | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/inno-HVAC-efficiency-10- | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/inno-Jam-Petrochemical-polymerization-digitwin | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/inno-Khalij-Apadana-Reformer-Methanol-Digital-Twin-System | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/inno-Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System- | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/intelligent-management-sys-energy-carbon-sustainability- | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System | 0 | 0 | 0 | 0 | — | — |
| parsasohrab1/khalij-products-to-extend | 0 | 0 | 0 | 0 | — | — |

## B) کد بدون تست
| مخزن | فایل کد | حجم کد (KB) | تست | CI | TRL مستند | داده واقعی |
|---|---|---|---|---|---|---|
| parsasohrab1/-ApexAsset-AI | 71 | 243 | 0 | 0 | — | ✔ (ISIE: NASA IMS (۴ خرابی)) |
| Ai-ithub/Aerobot | 2 | 8 | 0 | 0 | — | — |
| parsasohrab1/Digital-twin---nuc---reac | 56 | 184 | 0 | 0 | — | — |
| Ai-ithub/iEOR | 5 | 6177 | 0 | 0 | — | — |
| Ai-ithub/iEXPLO---intelligent-exploration- | 6 | 874 | 0 | 0 | — | — |
| parsasohrab1/inno---inteligent---ref---park-naft | 50 | 123 | 0 | 0 | — | — |
| parsasohrab1/inno---Oil-Industry-Smart-Technology-and-Innovation-Park | 82 | 317 | 0 | 1 | — | — |
| parsasohrab1/inno-fanavaran-ioa | 16 | 15 | 0 | 0 | — | — |
| parsasohrab1/Iran-carbon-black | 124 | 937 | 0 | 0 | — | — |

## C) کد + تست، بدون سند TRL
| مخزن | فایل کد | حجم کد (KB) | تست | CI | TRL مستند | داده واقعی |
|---|---|---|---|---|---|---|
| parsasohrab1/AI-SEO-Content- | 86 | 1109 | 9 | 2 | — | — |
| parsasohrab1/BAREKAT-Big-Data-Analytics-in-Health | 210 | 602 | 34 | 2 | — | — |
| parsasohrab1/barekat-gen-therapy | 110 | 176 | 9 | 1 | — | — |
| parsasohrab1/barekat-Genomics | 214 | 701 | 24 | 0 | — | — |
| parsasohrab1/digital-twine-gas-turbine | 167 | 7224 | 20 | 2 | — | — |
| parsasohrab1/dof-digital-oil-field | 213 | 1608 | 30 | 4 | — | — |
| parsasohrab1/FIDPS---Intelligent-Formation-Integrity-damage-prevention-system- | 100 | 832 | 1 | 0 | — | ✔ (FORCE 2020 (zonation)) |
| parsasohrab1/HQCA-Hybrid-Quantum-Classical-Drug-Discovery | 24 | 158 | 3 | 0 | — | ✔ (IQIM: ChEMBL EGFR) |
| parsasohrab1/i-drill | 444 | 4266 | 88 | 11 | — | — |
| parsasohrab1/i-lift---AI-Powered-Artificial-Lift-Management-Dashboard | 160 | 586 | 21 | 2 | — | ✔ (Petrobras 3W v2) |
| parsasohrab1/iFDC---FCDDWCSW | 28 | 388 | 5 | 0 | — | — |
| Ai-ithub/iFDC---FDDDC | 11 | 45 | 1 | 0 | — | — |
| parsasohrab1/inno-Abadan-Petrochemical-Smart-Dash | 89 | 250 | 1 | 0 | — | — |
| parsasohrab1/inno-iran-yasa-60ta | 48 | 110 | 5 | 1 | برنامه‌ی اعتبارسنجی برای TRL 5 | ادعا در README؛ تأییدنشده |
| parsasohrab1/inno-Khalij-Arvand-ChlorAlkali-PVC-Digital-Twin-System- | 23 | 15 | 1 | 0 | — | — |
| parsasohrab1/inno-khark-dss | 56 | 46 | 2 | 1 | — | — |
| parsasohrab1/inno-khorasan-petrochemical-SEM | 25 | 123 | 6 | 0 | — | — |
| parsasohrab1/inno-shimibaft-petrochemical | 49 | 215 | 5 | 1 | — | — |
| parsasohrab1/inno-tech-inspection-corrosion-control-60ta | 40 | 322 | 3 | 1 | بخش «اعتبارسنجی با داده واقعی (مسیر TRL 5)» در README | ادعا در README؛ تأییدنشده |
| parsasohrab1/inno-terminals-tanks | 76 | 183 | 4 | 1 | — | — |
| parsasohrab1/Khalij-BandarImam-MultiPlant-Feedstock-Margin-Orchestrator-System | 10 | 37 | 1 | 0 | — | — |
| parsasohrab1/khalij-Digital-Transformation-and-Value-Chain-Integration-System | 85 | 296 | 1 | 0 | — | — |
| parsasohrab1/khalij-Intelligent-Energy-Carbon-and-Sustainability-Management-System | 121 | 512 | 15 | 1 | — | — |
| parsasohrab1/Khalij-Production-Process-Prediction-and-Optimization-System | 90 | 347 | 11 | 1 | — | — |
| parsasohrab1/Mili-F-graph-binary-scriptors | 153 | 390 | 28 | 1 | — | — |
| parsasohrab1/Mili-Multi-Mode-Adaptive-Decision-System | 70 | 228 | 15 | 1 | — | — |
| parsasohrab1/MS-microcontroller | 190 | 1057 | 11 | 2 | — | — |
| parsasohrab1/nuc---pdm---reactor | 45 | 58 | 4 | 0 | — | — |
| parsasohrab1/OGIM---NISOC | 203 | 1552 | 30 | 4 | — | — |
| parsasohrab1/pfd---pid-design-for-gas-turbine | 1084 | 20061 | 384 | 0 | — | — |
| parsasohrab1/steedly | 160 | 726 | 8 | 1 | — | — |

## D) کد + تست + سند TRL
| مخزن | فایل کد | حجم کد (KB) | تست | CI | TRL مستند | داده واقعی |
|---|---|---|---|---|---|---|
| parsasohrab1/articles-explainguard-faithfulness | 7 | 14 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | — |
| parsasohrab1/articles-hydrogate-streamflow | 7 | 10 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | — |
| parsasohrab1/articles-qgrid-part | 9 | 14 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | ✔ (IEEE case9/14 (pandapower)) |
| parsasohrab1/articles-qrng-audit | 6 | 11 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | — |
| parsasohrab1/articles-qshot-lab | 6 | 11 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | ✔ (PySCF/OpenFermion) |
| parsasohrab1/articles-readmitcal-diabetes | 6 | 13 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | — |
| parsasohrab1/articles-stratguard-facies | 8 | 12 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | ✔ (SEG 2016 + FORCE 2020) |
| parsasohrab1/articles-stretchwatch-vqe | 5 | 7 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | ✔ (PySCF FCI/CCSD(T)) |
| parsasohrab1/articles-wearshift-har | 7 | 10 | 1 | 1 | TRL 4 (مستند در docs/TRL.md) | — |
| parsasohrab1/barekat-Advanced-Cell-Therapy-Products | 64 | 133 | 8 | 1 | TRL 5 ادعا‌شده (نرم‌افزار، محیط شبیه‌سازی‌شده) | — |
| parsasohrab1/barekat-Diagnostic-Kits | 133 | 478 | 20 | 1 | TRL 5 روی داده شبیه‌سازی؛ روی داده واقعی نه | — |
| parsasohrab1/Intelligent-software-for-diagnosing-and-treating-esophageal-cancer | 303 | 2115 | 27 | 1 | TRL 4 کل محصول (ماژول پیش‌آگهی TRL 5) | ادعا در README؛ تأییدنشده |
| parsasohrab1/Mili--BNN-TMR | 114 | 335 | 23 | 2 | فایل TRL دارد (مقدار در README مشخص نیست) | — |
| parsasohrab1/N---Barekat---IPIND---Intelligent-Platform-for-Integrated-Nanocarrier-Design | 92 | 515 | 16 | 1 | TRL 4 (مستند؛ TRL 5 نه) | — |
| parsasohrab1/NPA---Neuro-Predict-Ai | 340 | 2361 | 60 | 8 | TRL 4 (مستند: TRL 5 هنوز قابل ادعا نیست) | ادعا در README؛ تأییدنشده |

## نکات و ناسازگاری‌ها
- **تکراری/هم‌پوشان:** `inno---inteligent---ref---park-naft` (کد دارد) و `inno---inteligent-ref---park-naft` (فقط README)؛ سه مخزن AryaSasol-PE (`Khalij-…`، `inno-Khalij-…`، و `…Loop…`)؛ سه مخزن انرژی/کربن (`intelligent-management-sys-…`، `khalij-Intelligent-…`)؛ دو مخزن Apadana. پیشنهاد: هر خانواده یک مخزن اصلی تعیین شود.
- مخازن `articles-*` (۹ تا) هنوز **public** هستند؛ باید Private شوند (من ابزارش را ندارم).
- `khalij-products-to-extend` فقط ۱۷ سند دارد و هیچ کد؛ `pfd---pid-design-for-gas-turbine` ۱۰٫۹ MB کد/نقشه دارد ولی تست ندارد.
- مخازن A فقط با SRS/README «تعریف شده»اند؛ برای رسیدن به TRL 4 نیاز به اسکفلد، تست و CI دارند (همان کاری که برای `articles-*` کردیم).
- برای ۱۲ چکیده‌ی دیگر داده‌ی واقعی در دسترس نیست (`research/DATA_CATALOGUE.md`).