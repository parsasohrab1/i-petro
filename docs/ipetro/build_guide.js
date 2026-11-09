// Builds docs/ipetro/iPetro-User-Guide.pdf: screenshots of every tab of platform/index.html (sample data) + the tour texts.
// Run: node docs/ipetro/build_guide.js   (needs playwright and Chromium; Vazirmatn is fetched from Google Fonts)
const { chromium } = require(process.env.PW_MODULE || "playwright");
const fs = require("fs"), path = require("path");
const ROOT = path.resolve(__dirname, "../.."), OUT = __dirname;
const html = fs.readFileSync(process.env.HTML_PATH || path.join(ROOT, "platform/index.html"), "utf8");   // HTML_PATH: build from another copy of the page
// Put the official company logo at docs/ipetro/logo.png (PNG, transparent background preferred); without it the cover shows the wordmark only.
const LOGO = path.join(OUT, "logo.png"), logoB64 = fs.existsSync(LOGO) ? fs.readFileSync(LOGO).toString("base64") : "";
const TOUR = eval(html.match(/const TOUR = (\[[\s\S]*?\n\]);/)[1]);
const MODS = {market:"Market – بازار",events:"Events – رویدادها",erp:"ERP – مدیریت شرکت",bpms:"BPMS – کار روزانه",letters:"Letters – نامه‌نگاری",patent:"Patent – پتنت",articles:"Articles – مقاله‌ها"};

// ---------------------------------------------------------------- sample data (fictional)
const T = (id,o) => [id,{source:"نمونه",status:"analysed",line:"ai",market:"international",...o}];
const store = {
 "market/data/tenders": Object.fromEntries([
  T("t1",{title:"AI-based predictive maintenance for gas compressor stations",country:"Kenya",buyer:"Kenya Pipeline Co.",sector:"شرکت دولتی",days_left:21,deadline:"2026-11-11",url:"#",
   analysis:{relevance_score:82,eligibility:"partner_required",summary_fa:"نگهداری پیش‌بینانه‌ی کمپرسورها؛ با محصول پایش تجهیزات هم‌خوان است.",conditions:{price_fa:"بودجه‌ی تخمینی ۴۰۰ هزار دلار",guarantee_fa:"ضمانت‌نامه‌ی شرکت ۲٪",experience_fa:"دو پروژه‌ی مشابه",international_fa:"پذیرش شرکت‌های خارجی با شریک محلی"},compliance_flags_fa:[]}}),
  T("t2",{title:"Digital twin for a refinery energy management system",country:"Türkiye",buyer:"Public energy agency",sector:"دولتی",days_left:9,deadline:"2026-10-30",url:"#",
   analysis:{relevance_score:68,eligibility:"direct",summary_fa:"دوقلوی دیجیتال برای مدیریت انرژی پالایشگاه.",conditions:{price_fa:"ذکر نشده",guarantee_fa:"۵٪",experience_fa:"رزومه‌ی مشابه",international_fa:"پذیرش بله"},compliance_flags_fa:["بررسی تحریم‌ها"]}}),
  T("t3",{title:"Hospital information system analytics platform",country:"Oman",buyer:"Ministry of Health",sector:"دولتی",days_left:4,deadline:"2026-10-25",url:"#",
   analysis:{relevance_score:41,eligibility:"not_feasible",summary_fa:"نیاز به ثبت محلی و گواهی‌های امنیتی.",conditions:{international_fa:"شرکت خارجی مجاز نیست"},compliance_flags_fa:["ثبت محلی","مجوز امنیتی"]}}),
  T("t4",{title:"خرید خدمات پایش هوشمند شبکه‌ی توزیع آب",country:"ایران",buyer:"شرکت آب منطقه‌ای نمونه",sector:"شرکت دولتی",market:"domestic",days_left:12,deadline_fa:"۲۹ آبان ۱۴۰۵",setad_number:"2005091234000001",url:"#",
   analysis:{relevance_score:75,eligibility:"direct",summary_fa:"پایش و پیش‌بینی مصرف آب با یادگیری ماشین.",conditions:{price_fa:"طبق برآورد کارفرما",guarantee_fa:"۵٪",experience_fa:"رتبه‌ی فناوری اطلاعات",international_fa:"—"},compliance_flags_fa:[]}}),
  T("t5",{title:"طراحی سایت شرکتی و سئو برای تولیدکننده‌ی قطعات",country:"ایران",buyer:"تولیدی نمونه",line:"web",market:"domestic",days_left:15,deadline_fa:"۲ آذر ۱۴۰۵",url:"#"}),
 ]),
 "market/data/events": {e1:{name:"Gastech 2026",name_fa:"گسـتک ۲۰۲۶",city:"Milan",country:"Italy",start:"2026-11-09",end:"2026-11-12",region:"world",categories:["energy"],why_fa:"بزرگ‌ترین رویداد گاز و LNG",participation_fa:"بازدید و ملاقات با خریداران",url:"#",source:"#"},
  e2:{name:"Iran Oil Show",name_fa:"نمایشگاه نفت تهران",city:"تهران",country:"ایران",start:"2026-12-05",end:"2026-12-08",region:"iran",categories:["energy"],why_fa:"بازار داخلی نفت و گاز",participation_fa:"غرفه‌ی نمونه‌ی دموی داشبورد",url:"#"}},
 "market/data/investors": {v1:{name:"Energy Ventures (نمونه)",hq:"London",type:"vc",stage_fa:"Seed تا Series A",ticket_fa:"۵۰۰ هزار تا ۳ میلیون دلار",fund_fa:"۱۵۰ میلیون دلار",investments_fa:"نرم‌افزار صنعتی",focus_fa:"هوش مصنوعی انرژی",website:"#",apply:"#",compliance_fa:"بررسی تحریم‌ها پیش از ارتباط"}},
 "market/data/leads": {l1:{name:"آقای نمونه",activity:"تولید قطعات صنعتی",city:"اصفهان",phone:"0310000000",source:"نمونه",url:"#"}},
 products: {p1:{name:"پایش هوشمند توربین گاز",trl:5,client:"کارفرمای نمونه",feedback1:"طراحی داشبورد تأیید شد",feedback2:"درخواست داده‌ی واقعی",tech_backend:"Python, FastAPI",tech_frontend:"React",tech_protocols:"OPC-UA, MQTT",tech_infra:"Docker, Kafka",algorithms:"LSTM, Isolation Forest",github:"https://github.com/example/turbine",equipment:[{item:"گیتوی صنعتی",qty:"۲",price:"—"}],similar:[{title:"GE Predix",summary:"پلتفرم APM",link:"#"}]},
  p2:{name:"غربالگری هوشمند بیماری‌های عصبی",trl:4,client:"—",algorithms:"CNN, Random Forest",tech_backend:"Python"}},
 patents:{pt1:{title:"روش پیش‌بینی خرابی کمپرسور با داده‌ی ترکیبی",product:"p1",number:"140550001234",office:"اداره‌ی ثبت اختراع ایران",date:"2026-09-10",status:"filed"}},
 "patentops/data/items":{o1:{product_name:"پایش هوشمند توربین گاز",claim:"ترکیب سیگنال ارتعاش و دما برای پیش‌بینی",prior_art:"چند سابقه‌ی نزدیک",verdict:"قابل ثبت",verdict_code:"patentable",date:"2026-10-21",sources:["#"]}},
 finance:{f1:{title:"بیمه‌ی تأمین اجتماعی مهر",type:"insurance",period:"مهر ۱۴۰۵",amount:42000000,due:"2026-10-25",status:"unpaid"}},
 clients:{c1:{client:"کارفرمای نمونه",product:"p1",stage:"demo",value:1800000000,next:"ارائه‌ی دمو",next_date:"2026-10-28"}},
 members:{me1:{full_name:"سارا نمونه",role:"manager",team:"ai",staff_type:"product",office_days:["sat","mon","wed"],start_time:"08:30",joined:"2026-10-20",telegram:"",fingerprint_asset:"fp",nda_version:"1",nda_at:"2026-10-20T08:00:00Z"},
  u2:{full_name:"علی نمونه",role:"member",team:"web",staff_type:"trainee_web",office_days:["sun","tue"],start_time:"09:00",joined:"2026-10-01"}},
 tasks:{k1:{title:"تکمیل داشبورد دموی توربین",desc:"نسخه‌ی مشتری",assignee:"me1",created_by:"me1",team:"ai",due:"2026-10-24",priority:"high",status:"doing",points:8,type:"story",sprint:"s1",updated:"1"},
  k2:{title:"سئوی صفحه‌ی محصولات",assignee:"u2",created_by:"me1",team:"web",due:"2026-10-27",priority:"normal",status:"todo",points:3,type:"task",sprint:"s1",updated:"2"},
  k3:{title:"نوشتن آزمون‌های واحد ماژول پایش",assignee:"me1",created_by:"me1",team:"ai",due:"2026-10-23",priority:"normal",status:"done",points:5,type:"task",sprint:"s1",done_at:"2026-10-20T10:00:00Z",updated:"3"},
  k4:{title:"اتصال داده‌ی OPC-UA آزمایشی",assignee:"u2",created_by:"me1",team:"ai",due:"2026-10-26",priority:"high",status:"doing",points:5,type:"story",sprint:"s1",blocked:true,blocker_note:"منتظر دسترسی شبکه",updated:"4"},
  k5:{title:"تهیه‌ی پروپوزال مناقصه‌ی کنیا",assignee:"me1",created_by:"me1",team:"content",priority:"high",status:"todo",points:null,type:"story",sprint:"",created:"2026-10-19T08:00:00Z",updated:"5"},
  k6:{title:"طراحی لندینگ iPetro",assignee:"u2",created_by:"me1",team:"web",priority:"normal",status:"todo",points:5,type:"task",sprint:"",created:"2026-10-19T09:00:00Z",updated:"6"},
  k0:{title:"راه‌اندازی داشبورد اولیه",assignee:"me1",created_by:"me1",team:"ai",priority:"normal",status:"approved",points:13,type:"story",sprint:"s0",done_at:"2026-10-07T10:00:00Z",updated:"0"}},
 sprints:{s0:{name:"اسپرینت ۱",goal:"داشبورد اولیه آماده‌ی دمو",start:"2026-09-24",end:"2026-10-07",status:"closed",committed:16,final_total:13,completed:13,velocity:13,retro:{went_well:"دمو به‌موقع آماده شد",improve:"برآورد کارها دقیق‌تر باشد",actions:"برآورد با Planning Poker"}},
  s1:{name:"اسپرینت ۲",goal:"دموی توربین و ارتباط OPC-UA",start:"2026-10-15",end:"2026-10-28",status:"active",committed:21},
  s2:{name:"اسپرینت ۳",goal:"",start:"2026-10-29",end:"2026-11-11",status:"planned"}},
 letters:{n1:{number:"PPT-1405-0001",date:"2026-10-20",recipient:"جناب آقای دکتر رضایی\nمدیرعامل شرکت نمونه",subject:"درخواست جلسه‌ی معرفی",body:"با سلام\nبدین‌وسیله درخواست جلسه‌ی معرفی محصولات هوشمند را اعلام می‌داریم.",office_sig:{by:"me1",at:"2026-10-20T08:00:00Z"}}},
 letters_archive:{
  a1:{number:"PPT-1405-0000",date:"2026-10-10",subject:"پیشنهاد همکاری فناورانه",recipient:"مدیرعامل شرکت نمونه",channel:"automation",stage:"review",status:"active",owner:"me1",next_action:"تماس برای پیگیری",next_date:"2026-10-23",log:[{at:"2026-10-12T09:00:00Z",by:"me1",stage:"review",note:"نامه در دست بررسی است"}],employer_no:"1405/1234"},
  a2:{id:"a2",number:"PPT-1405-0002",date:"2026-10-21",subject:"معرفی محصولات هوشمند",recipient:"مدیرعامل شرکت نمونه ۲",stage:"ready",status:"active",owner:"me1",task_stage:"claimed",task_assignee:"سارا نمونه",task_title:"ارسال نامه معرفی"},
  a3:{id:"a3",subject:"درخواست جلسه فنی",recipient:"مدیر فنی شرکت نمونه ۳",stage:"ready",status:"active",owner:"me1",task_stage:"todo"},
  a4:{number:"PPT-1405-0003",date:"2026-10-15",subject:"پیگیری پروپوزال",recipient:"شرکت نمونه ۴",stage:"sent",status:"active",owner:"me1"},
  a5:{number:"PPT-1405-0004",date:"2026-10-16",subject:"دعوت به همکاری",recipient:"شرکت نمونه ۵",stage:"received",status:"active",owner:"me1"},
 },
 tracking:{t1:{owner:"me1",stage:"partner_email",value_usd:400000,next_action:"پیگیری ایمیل شریک",next_date:"2026-10-22"},t2:{owner:"u2",stage:"proposal",value_usd:250000},"ev_e1":{owner:"me1"}},
 "settings/company":{name_fa:"پترو پالا توس",name_en:"Petro Pala Toos",logo_asset:"logo",address:"تهران، خیابان نمونه",ceo_member:"me1",last_backup:new Date().toISOString()},
 "reports/me1/items":{"2026-10-21":{date:"2026-10-21",text:"طراحی داشبورد دمو",hours:8,score:78,feedback:"خروجی مشخص بود."},"2026-10-20":{date:"2026-10-20",text:"داشبورد دمو را کامل کردم و تست واحد نوشتم.",hours:7.5,score:72,feedback:"خروجی مشخص بود؛ ساعت کار کمی کمتر از ۸ بود."}},
 "reports/u2/items":{}, "attendance/me1/days":{"2026-10-21":{in:"08:35",break_min:60}}, "attendance/u2/days":{}
};
if (!logoB64) delete store["settings/company"].logo_asset;
const mock = `(()=>{ const store=${JSON.stringify(store)}; if(window.__noMe) delete store.members.me1;
 const docs=p=>Object.entries(store[p]||{}).map(([id,v])=>({id,data:()=>v}));
 const col=p=>({onSnapshot(cb){setTimeout(()=>cb({docs:docs(p)}),10)},get:()=>Promise.resolve({docs:docs(p)})});
 const db={collection:col,doc(p){const v=store[p];return{onSnapshot(cb){cb({exists:!!v,data:()=>v||{}})},async set(d){(window.__saved=window.__saved||[]).push([p,d])},async update(){},async get(){return{exists:!!v,data:()=>v||{}}},async delete(){},async acquire(){return{acquired:true}}}}};
 window.claude={use:async n=>n==="db"?db:n==="user"?{me:async()=>({id:"me1",isOwner:true,canEdit:true,name:"سارا نمونه"}),can:async()=>true}:n==="downloads"?{save:async()=>{}}:n==="assets"?{upload:async()=>({id:"x"})}:{}};})();`;

const E = s => String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
async function open(browser, noMe) {
  const pg = await browser.newPage({ viewport: { width: 1180, height: 700 } });
  await pg.addInitScript((noMe ? "window.__noMe=1;" : "") + mock);
  await pg.route("**/*", r => {
    const u = r.request().url();
    if (u.startsWith("http://t.local/_blob/")) return logoB64 ? r.fulfill({ contentType: "image/png", body: Buffer.from(logoB64, "base64") }) : r.abort();
    if (u.startsWith("http://t.local/")) return r.fulfill({ contentType: "text/html; charset=utf-8", body: html });
    if (/fonts\.(googleapis|gstatic)\.com/.test(u)) return r.continue();
    return r.abort();
  });
  await pg.goto("http://t.local/"); await pg.waitForTimeout(1200);
  return pg;
}
const shot = async (pg) => "data:image/png;base64," + (await pg.screenshot()).toString("base64");

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" }).catch(() => chromium.launch());
  const pg = await open(browser, false);
  const shots = {};
  for (const st of TOUR) if (st.mod) {
    const key = st.mod + "." + (st.sub || "");
    try {
      await pg.click(`[data-act=mod][data-k=${st.mod}]`);
      if (st.sub) {
        const exists = await pg.locator(`[data-act=sub][data-k=${st.sub}]`).count();
        if(exists > 0) await pg.click(`[data-act=sub][data-k=${st.sub}]`);
        else { console.log(`skipped ${key} (tab not found)`); continue; }
      }
      await pg.waitForTimeout(250); shots[key] = await shot(pg);
    } catch(e) {
      console.log(`skipped ${key}:`, e.message);
    }
  }
  await pg.click("[data-act=mod][data-k=market]"); await pg.click("[data-act=sub][data-k=overseas]"); await pg.waitForTimeout(200);
  await pg.locator("details summary", { hasText: "دلایل" }).first().click(); const gng = await shot(pg);
  await pg.click("[data-act=mod][data-k=market]"); await pg.click("[data-act=sub][data-k=tracking]"); await pg.click("[data-act=track]"); await pg.waitForTimeout(200); const trackForm = await shot(pg);
  await pg.click("[data-act=close]"); await pg.click("#bell"); await pg.waitForTimeout(200); const inbox = await shot(pg); await pg.click("[data-act=close]");
  await pg.click("[data-act=mod][data-k=letters]"); await pg.click("[data-act=sub][data-k=new]"); await pg.selectOption("#c_identity", "intl");
  await pg.fill("[data-c=recipient]", "Mr. John Smith\nProcurement Manager\nExample Energy Co."); await pg.fill("[data-c=subject]", "Proposal for predictive maintenance services");
  await pg.fill("[data-c=body]", "We would like to introduce our AI-based predictive maintenance platform.\nWe would welcome a short call to discuss your requirements."); await pg.waitForTimeout(200); const intl = await shot(pg);
  await pg.click("[data-act=mod][data-k=articles]"); await pg.waitForTimeout(300); const artShot = await shot(pg);
  await pg.locator("table").first().scrollIntoViewIfNeeded(); await pg.mouse.wheel(0, 150); await pg.waitForTimeout(250); const artRows = await shot(pg);
  
  // Letter sending workflow screenshots
  let sendTab = "", shastaCards = "", cardFiltered = "";
  try {
    await pg.click("[data-act=mod][data-k=letters]"); await pg.waitForTimeout(200);
    const hasSendTab = await pg.locator('[data-act=sub][data-k=send]').count();
    if(hasSendTab > 0) {
      await pg.click("[data-act=sub][data-k=send]"); await pg.waitForTimeout(300);
      sendTab = await shot(pg);
    }
  } catch(e) { console.log("send tab screenshot skipped:", e.message); }
  
  // Highlight stat cards in Shasta letters
  try {
    await pg.click("[data-act=sub][data-k=pp]"); await pg.waitForTimeout(300);
    await pg.click("[data-act=pp-grp][data-k=shasta]"); await pg.waitForTimeout(300);
    shastaCards = await shot(pg);
    
    // Click a stat card to show filtering
    const hasClickable = await pg.locator('.kpi.clickable').count();
    if(hasClickable > 0) {
      await pg.evaluate(() => {
        const cards = document.querySelectorAll('.kpi.clickable');
        if(cards[1]) cards[1].click();
      });
      await pg.waitForTimeout(300);
      cardFiltered = await shot(pg);
    }
  } catch(e) { console.log("shasta cards screenshot skipped:", e.message); }
  
  const pg2 = await open(browser, true);
  const reg = await shot(pg2); await pg2.fill("#f_full_name", "کاربر جدید");
  await pg2.evaluate(() => document.querySelector("#drawer").requestSubmit()); await pg2.waitForTimeout(1200);
  const tour = await shot(pg2);
  await browser.close();

  const img = (src, cap) => `<figure><img src="${src}"><figcaption>${E(cap)}</figcaption></figure>`;
  let toc = "", body = "", n = 0, lastMod = "";
  for (const st of TOUR) {
    if (st.mod && !st.sub) { n++; lastMod = st.mod; toc += `<li>${E(MODS[st.mod])}</li>`;
      body += `<section class="mod"><h2>${E(MODS[st.mod])}</h2><p>${E(st.text)}</p>${st.mod === "articles" ? img(artShot, "تصویر نمونه با داده‌ی فرضی") + img(artRows, "ستون جزئیات: محصول مقاله و لینک ریپو یا شاخه؛ ستون آخر: دکمه‌ی چکیده (Word)") : ""}</section>`; continue; }
    if (st.mod && st.sub) body += `<section class="tab"><h3>${E(st.title)}</h3><p>${E(st.text)}</p>${img(shots[st.mod + "." + st.sub], "تصویر نمونه با داده‌ی فرضی")}</section>`;
  }
  const firstSteps = TOUR[TOUR.length - 1].text, bell = TOUR.find(s => s.sel === "#bell");
  const doc = `<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700;800&display=swap" rel="stylesheet"><style>
  @page{size:A4;margin:16mm 14mm 16mm}
  body{font:12.5px/1.9 Vazirmatn,"DejaVu Sans",sans-serif;color:#171515;margin:0}
  .cover{height:255mm;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border:3px solid #d12a1f;border-radius:14px;page-break-after:always}
  .cover img{width:230px}.cover h1{font-size:64px;margin:14px 0 0;letter-spacing:2px}.cover h2{font-weight:500;margin:6px 0;font-size:22px}.cover p{color:#615b59;margin:2px}
  h2{font-size:21px;border-bottom:3px solid #d12a1f;padding-bottom:4px;margin:0 0 8px}h3{font-size:15px;margin:0 0 2px}
  .mod{page-break-before:always}.tab{page-break-inside:avoid;margin:14px 0 18px}
  figure{margin:6px 0 0}figure img{width:100%;border:1px solid #cfcac7;border-radius:6px}figcaption{font-size:10.5px;color:#615b59;text-align:center}
  .box{background:#f5f4f3;border-right:4px solid #d12a1f;padding:8px 12px;margin:10px 0;border-radius:4px}
  .steps-box{background:#e8f5e9;border-right:4px solid #4caf50;padding:12px 16px;margin:12px 0;border-radius:6px;page-break-inside:avoid}
  .steps-box h3{margin-top:0;color:#2e7d32}
  .steps-box ol.steps{margin:8px 0 0;padding-right:24px}
  .steps-box ol.steps li{margin:8px 0;line-height:1.7}
  .steps-box ol.steps li b{color:#1b5e20}
  .mistakes-box{background:#ffebee;border-right:4px solid #f44336;padding:12px 16px;margin:12px 0;border-radius:6px;page-break-inside:avoid}
  .mistakes-box h3{margin-top:0;color:#c62828}
  .mistakes-box ul{margin:8px 0 0;padding-right:24px}
  .mistakes-box ul li{margin:6px 0;line-height:1.7}
  .mistakes-box ul li b{color:#b71c1c}
  .checklist{background:#fff9c4;border:2px solid #fbc02d;padding:14px;margin:16px 0;border-radius:8px;page-break-inside:avoid}
  .checklist h3{margin-top:0;color:#f57f17}
  .check-table{width:100%;border-collapse:collapse;margin:10px 0}
  .check-table td{padding:6px 8px;border-bottom:1px solid #e0e0e0}
  .check-table td:first-child{width:30px;font-size:18px;font-weight:bold}
  .meta{font-size:10.5px;color:#615b59;margin:4px 0}
  li{margin:2px 0}.pb{page-break-before:always}</style></head><body>
  <div class="cover">${logoB64 ? `<img src="data:image/png;base64,${logoB64}" alt="logo">` : ""}<h1>iPetro</h1><h2>راهنمای کار با سامانه</h2><p>پترو پالا توس · Petro Pala Toos</p><p>نسخه‌ی ۲ · ${new Intl.DateTimeFormat("fa-IR-u-ca-persian", { year: "numeric", month: "long", day: "numeric" }).format(new Date())} (${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })})</p></div>
  <h2>iPetro چیست؟</h2><p>${E(TOUR[0].text.replace(/^iPetro /, "iPetro "))}</p>
  <div class="box"><b>هفت بخش اصلی:</b><ol>${toc}</ol></div>
  <h3>ورود و ثبت‌نام</h3><p>بار نخست که با حساب claude.ai وارد می‌شوید، فرم ثبت‌نام باز می‌شود. نام، تیم، نوع نیرو، روزهای حضور، ساعت ورود، ایمیل، شناسه‌ی تلگرام و تصویر امضا را وارد کنید. پس از ثبت، آموزش گام‌به‌گام خودکار شروع می‌شود.</p>${img(reg, "فرم ثبت‌نام هنگام ورود")}
  <h3 class="pb">آموزش درون سامانه</h3><p>آموزش هر بخش و هر تب را یک‌به‌یک نشان می‌دهد و تب مربوط را نشان‌دار می‌کند. هر زمان از دکمه‌ی «راهنما» بالای صفحه دوباره قابل اجراست.</p>${img(tour, "کارت آموزش پایین صفحه")}
  <h3>${E(bell.title)}</h3><p>${E(bell.text)}</p>${img(inbox, "پنجره‌ی اعلان‌ها")}
  ${body}
  
  <section class="mod pb"><h2>نحوه‌ی ارسال نامه (گام‌به‌گام)</h2>
  <p>این بخش به‌صورت ساده و گام‌به‌گام نحوه‌ی ارسال نامه را توضیح می‌دهد. برای همکاران غیرفنی.</p>
  
  <div class="steps-box">
    <h3>مراحل ارسال نامه</h3>
    <ol class="steps">
      <li><b>بروید به بخش نامه‌ها</b><br>از منوی بالای صفحه روی «Letters – نامه‌نگاری» کلیک کنید.</li>
      <li><b>بروید به تب «ارسال نامه»</b><br>در قسمت بالا تب «ارسال نامه» را انتخاب کنید.</li>
      <li><b>نام خودتان را انتخاب کنید</b><br>همیشه نام خودتان را انتخاب کنید، نه نام شخص دیگری. نامه‌هایی که به شما واگذار شده‌اند و نامه‌های بدون مسئول را خواهید دید.</li>
      <li><b>نامه را پیدا کنید</b><br>اگر نامه مسئول ندارد (بدون مسئول)، دکمه‌ی «برداشتن» را بزنید. بعد از برداشتن، نامه به بخش «در دست اقدام» با نام شما منتقل می‌شود.</li>
      <li><b>دریافت فایل Word</b><br>دکمه‌ی «دریافت Word (امروز)» را بزنید. فایل Word با تاریخ امروز و شماره‌ی امروز دریافت می‌شود. <b>مهم:</b> تاریخ و شماره هر روز تغییر می‌کند تا زمانی که نامه ارسال نشود، پس فایل Word را همان روزی که می‌خواهید نامه را بفرستید دانلود کنید.</li>
      <li><b>بررسی، امضا و ارسال نامه</b><br>نامه را بررسی کنید، امضا کنید، مهر بزنید و طبق روال معمول ارسال کنید (ایمیل، پست، تحویل حضوری).</li>
      <li><b>همان روز دکمه‌ی «ارسال شد» را بزنید</b><br>بلافاصله بعد از ارسال واقعی نامه، در همان صفحه دکمه‌ی «ارسال شد» را بزنید. بعد از این کار تاریخ و شماره برای همیشه ثابت می‌شود و نامه به بخش «ارسال‌شده» منتقل می‌شود.</li>
      <li><b>مراحل بعدی را به‌روز کنید</b><br>بعد از ارسال، باید مراحل پیگیری را به‌روز کنید: ثبت در دبیرخانه → ارجاع/بررسی → پاسخ → پیگیری → جلسه هماهنگ‌شده → جلسه برگزارشده → مذاکره → عقد قرارداد. در هر مرحله یک یادداشت کوتاه بنویسید.</li>
      <li><b>اگر نتوانستید، برگردانید</b><br>اگر نمی‌توانید نامه را ارسال کنید، دکمه‌ی «برگرداندن» را بزنید تا شخص دیگری بتواند آن را بردارد.</li>
    </ol>
  </div>
  ${sendTab?img(sendTab, "صفحه‌ی ارسال نامه – انتخاب نام و لیست نامه‌های نفرستاده"):"<p class=\"meta\">(تصویر صفحه‌ی ارسال نامه)</p>"}
  
  <div class="mistakes-box">
    <h3>⚠️ اشتباهات رایج (از این کارها خودداری کنید)</h3>
    <ul>
      <li><b>انتخاب نام شخص دیگری:</b> همیشه نام خودتان را انتخاب کنید. اگر نام دیگری را انتخاب کنید، نامه‌های آن شخص را خواهید دید که مربوط به شما نیست.</li>
      <li><b>دانلود Word در یک روز و ارسال در روز دیگر:</b> اگر فایل Word را امروز دانلود کنید و نامه را فردا بفرستید، تاریخ و شماره اشتباه خواهد بود. فایل را همان روز ارسال دانلود کنید.</li>
      <li><b>فراموش کردن دکمه‌ی «ارسال شد»:</b> اگر فراموش کنید این دکمه را بزنید، تاریخ و شماره ثابت نمی‌شود و نامه در لیست «نفرستاده» باقی می‌ماند.</li>
      <li><b>زدن «ارسال شد» قبل از ارسال واقعی:</b> این دکمه را فقط بعد از ارسال واقعی نامه (ایمیل، پست، تحویل حضوری) بزنید. اگر زودتر بزنید، تاریخ و شماره ثابت می‌شود ولی نامه هنوز ارسال نشده است.</li>
    </ul>
  </div>
  
  <h3 class="pb">کارت‌های آماری قابل کلیک</h3>
  <p>در بخش بایگانی نامه‌ها (مثلاً نامه‌های شستا)، کارت‌های آماری بالای صفحه قابل کلیک هستند. وقتی روی یک کارت کلیک می‌کنید، فقط نامه‌های مربوط به آن مرحله نمایش داده می‌شود.</p>
  ${shastaCards?img(shastaCards, "کارت‌های آماری در بخش نامه‌های شستا"):"<p class=\"meta\">(تصویر کارت‌های آماری شستا)</p>"}
  <p>مثلاً اگر روی کارت «ارسال‌شده» کلیک کنید، فقط نامه‌هایی که ارسال شده‌اند نمایش داده می‌شوند. برای نمایش همه، روی کارت «همه» یا دوباره روی همان کارت کلیک کنید.</p>
  ${cardFiltered?img(cardFiltered, "لیست نامه‌ها بعد از کلیک روی یک کارت – فقط نامه‌های آن مرحله"):"<p class=\"meta\">(تصویر لیست فیلترشده)</p>"}
  
  <div class="checklist pb">
    <h3>📋 چک‌لیست ارسال نامه (قابل چاپ)</h3>
    <p class="meta">این صفحه را چاپ کنید و در کنار میز کار قرار دهید.</p>
    <table class="check-table">
      <tr><td>☐</td><td>به بخش Letters → ارسال نامه رفتم</td></tr>
      <tr><td>☐</td><td>نام خودم را انتخاب کردم</td></tr>
      <tr><td>☐</td><td>نامه را پیدا کردم و اگر لازم بود «برداشتن» زدم</td></tr>
      <tr><td>☐</td><td>«دریافت Word (امروز)» را زدم (همان روز ارسال)</td></tr>
      <tr><td>☐</td><td>نامه را بررسی کردم</td></tr>
      <tr><td>☐</td><td>نامه را امضا و مهر کردم</td></tr>
      <tr><td>☐</td><td>نامه را ارسال کردم (ایمیل/پست/حضوری)</td></tr>
      <tr><td>☐</td><td>بلافاصله بعد از ارسال، دکمه‌ی «ارسال شد» را زدم</td></tr>
      <tr><td>☐</td><td>مراحل بعدی را با یادداشت کوتاه به‌روز کردم</td></tr>
    </table>
    <p class="meta" style="margin-top:10px"><b>یادآوری:</b> تاریخ و شماره بعد از «ارسال شد» برای همیشه ثابت می‌شود.</p>
  </div>
  </section>
  
  <section class="mod"><h2>چند کار پرکاربرد</h2>
   <div class="tab"><h3>مسئولیت گرفتن و پیگیری پروژه</h3><p>در Market دکمه‌ی «مسئولیت را می‌گیرم» را بزنید؛ مورد از فهرست باز برداشته می‌شود. سپس در Project Tracking با «ویرایش» مرحله، اقدام بعدی، ارزش و احتمال برد را ثبت کنید. هنگام پایان، نتیجه و دلیل را بنویسید تا ایجنت یاد بگیرد.</p>${img(trackForm, "فرم پیگیری پروژه")}</div>
   <div class="tab"><h3>Go / No-Go</h3><p>برای هر مناقصه‌ی تحلیل‌شده امتیازی از ۱۰۰ نمایش داده می‌شود: تطابق با محصولات ۴۰٪، صلاحیت ۲۵٪، زمان ۱۵٪، پذیرش شرکت خارجی ۱۰٪ و انطباق ۱۰٪. زیر «دلایل» می‌بینید امتیاز از کجا آمده است.</p>${img(gng, "ستون Go/No-Go و دلایل امتیاز")}</div>
   <div class="tab"><h3>نامه‌ی بین‌المللی</h3><p>در «نامه‌ی جدید» هویت فرستنده را «بین‌المللی» بگذارید تا نامه به انگلیسی و با سربرگ Parsa International Group ساخته شود. شماره‌ی نامه با PIG شروع می‌شود.</p>${img(intl, "نامه‌ی بین‌المللی و پیش‌نمایش")}</div>
   <div class="tab"><h3>چکیده‌ی آماده برای ژورنال یا کنفرانس</h3><p>در Articles برای هر ژورنال یا کنفرانس یک محصول مشخص شده است: محصول تازه ریپوی جدید دارد و محصول قدیمی شاخه‌ی «article-submission-content» با متن چکیده. دکمه‌ی «چکیده (Word)» فایلی می‌دهد که صفحه‌ی اول آن عنوان، چکیده و کلیدواژه‌ها طبق قالب همان مرجع (حداکثر واژه، تک‌پاراگراف، تعداد کلیدواژه) و صفحه‌ی دوم برگه‌ی داخلی با ددلاین، لینک رسمی و کارهای پیش از ثبت است. جاهای [داخل کروشه] نتایج واقعی‌اند که باید از آزمایش‌های تیم پر شود؛ هیچ عددی در متن پیش‌نویس نتیجه نیست. پیش از ثبت، محدودیت واژه را در راهنمای نویسندگان همان ژورنال یا کنفرانس بازبینی کنید. «همه‌ی چکیده‌ها (ZIP)» همه‌ی فایل‌ها را یک‌جا می‌دهد.</p></div>
  </section>
  <div class="box"><b>شروع کنید.</b> ${E(firstSteps)}</div>
  <p style="font-size:10.5px;color:#615b59">همه‌ی تصاویر با داده‌ی فرضی ساخته شده‌اند. این فایل با دستور <code>node docs/ipetro/build_guide.js</code> از روی خود سامانه دوباره ساخته می‌شود.</p></body></html>`;
  const b2 = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" }).catch(() => chromium.launch());
  const p = await b2.newPage(); await p.setContent(doc, { waitUntil: "networkidle" }); await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: path.join(OUT, "iPetro-User-Guide.pdf"), format: "A4", printBackground: true, displayHeaderFooter: true,
    headerTemplate: "<span></span>", footerTemplate: '<div style="font-size:9px;width:100%;text-align:center;color:#777">iPetro · <span class="pageNumber"></span> / <span class="totalPages"></span></div>', margin: { top: "16mm", bottom: "16mm", left: "14mm", right: "14mm" } });
  await b2.close(); console.log("ok");
})();
