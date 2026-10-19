"""Static Persian (RTL) dashboard written to docs/index.html.

Pages:
  domestic       Iran AI projects (Setad)            tabs: opportunities | conditions at a glance
  international  international AI tenders            tabs: opportunities | conditions at a glance | partners
  web            website design & SEO requests        tabs: opportunities | conditions at a glance
  events         AI events in Iran and worldwide
  investors      VCs, corporate venture arms and accelerators
"""
import json

from . import events, investors, partners, store
from .config import ROOT

TEMPLATE = r"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>توسعه بازار برون مرزی</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2430;--muted:#5d6878;--line:#e3e7ec;--accent:#0f6e6e;--accent-ink:#fff;
--new:#3b6fd8;--partner:#b26b00;--direct:#1f8a4c;--skip:#8a94a3;--warn:#c0392b;--head:#eef1f4;--star:#d99a00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11161d;--card:#18202a;--ink:#e6ebf1;
--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;--accent-ink:#0b1116;--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;
--skip:#76808e;--warn:#ef7b6e;--head:#1f2833;--star:#f0c040}}
:root[data-theme="dark"]{--bg:#11161d;--card:#18202a;--ink:#e6ebf1;--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;
--accent-ink:#0b1116;--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;--skip:#76808e;--warn:#ef7b6e;--head:#1f2833;--star:#f0c040}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 Vazirmatn,Tahoma,sans-serif}
header,main{max-width:1200px;margin:auto;padding:0 16px}header{padding-top:18px}
h1{margin:0;font-size:22px}.sub{color:var(--muted);font-size:13px}
.pages{display:flex;gap:8px;margin:14px 0 4px;flex-wrap:wrap}
.pages button,.tabs button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;padding:8px 14px}
.pages button{font-weight:600}
.pages button[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tabs{display:flex;gap:6px;margin:10px 0;flex-wrap:wrap}.tabs button{padding:5px 12px;font-size:14px}
.tabs button[aria-selected="true"]{border-color:var(--accent);color:var(--accent);font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:10px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:22px}.kpi span{color:var(--muted);font-size:12px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.bar input,.bar select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.bar input{flex:1;min-width:180px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.top{display:flex;gap:8px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.title{font-weight:600;overflow-wrap:anywhere}.meta{color:var(--muted);font-size:13px}
.pill{font-size:12px;padding:2px 9px;border-radius:99px;border:1px solid currentColor;white-space:nowrap;display:inline-block}
.s-new{color:var(--new)}.s-partner_search,.s-mou_negotiation,.s-considering,.s-drafted,.s-meeting{color:var(--partner)}
.s-bid_prep,.s-proposal_drafting,.s-submitted,.s-won,.s-registered,.s-attending,.s-attended,.s-sent,.s-replied,.s-mou{color:var(--direct)}
.s-skipped,.s-expired,.s-lost,.s-not_interested{color:var(--skip)}
.sector{color:var(--muted);border-color:var(--line)}
.urgent{color:var(--warn);font-weight:600}details{margin-top:6px}summary{cursor:pointer;color:var(--accent)}
ul{margin:4px 0;padding-inline-start:20px}a{color:var(--accent)}
code{font-size:12px;background:var(--bg);padding:1px 5px;border-radius:5px;direction:ltr;display:inline-block}
.glance{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin:8px 0}
.glance div{border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:13px}
.glance b{display:block;color:var(--muted);font-size:12px;font-weight:600}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:980px;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th{background:var(--head);font-weight:600}td.t{min-width:220px;font-weight:600}.empty{color:var(--muted);padding:20px}
.note{color:var(--muted);font-size:12px;margin:6px 0}
.star{cursor:pointer;color:var(--star);background:none;border:0;font-size:16px;padding:0 4px}
.offer{color:var(--direct);font-size:13px;font-weight:600}
@media (max-width:900px){table{min-width:0}thead{display:none}tr{display:block;border-bottom:1px solid var(--line);padding:8px 0}
td{display:block;border:0;padding:3px 12px}td.t{min-width:0}td[data-l]::before{content:attr(data-l) ": ";color:var(--muted);font-weight:600}}
</style>
</head>
<body>
<header><h1>توسعه بازار برون مرزی هوشمند</h1>
<div class="sub">آخرین اجرا: <span id="last"></span> · کشورهای ستاره‌دار: <span id="stars"></span></div>
<nav class="pages" role="tablist">
<button role="tab" data-page="domestic">پروژه‌های هوش مصنوعی ایران</button>
<button role="tab" data-page="international">بازار بین‌المللی</button>
<button role="tab" data-page="web">طراحی سایت و سئو</button>
<button role="tab" data-page="events">رویدادهای هوش مصنوعی</button>
<button role="tab" data-page="investors">سرمایه‌گذاران و شتاب‌دهنده‌ها</button>
</nav></header>
<main>
<div class="note" id="srcnote"></div>
<div class="kpis" id="kpis"></div>
<div class="tabs" role="tablist" id="tabs"></div>
<div class="bar"><input id="q" placeholder="جست‌وجو…"><select id="st"></select></div>
<div id="view"></div>
</main>
<script>
const DATA = __DATA__;
const ST = DATA.statuses, ACTIVE = new Set(DATA.active), STARRED = new Set(DATA.starred.map(s=>s.toLowerCase()));
const PAGES = {
 domestic:{note:'منبع: سامانه تدارکات الکترونیکی دولت (ستاد) – فقط فراخوان‌های حوزه‌ی هوش مصنوعی. جزئیات تضمین و ارزیابی در اسناد ستاد.',
   tabs:[['list','فرصت‌ها'],['glance','شرایط شرکت در مناقصه در یک نگاه']], intl:'شرایط پذیرش شرکت‌ها'},
 international:{note:'منابع: TED (اتحادیه اروپا)، بانک جهانی، Find a Tender (بریتانیا). ستاره کنار نام کشور = جست‌وجوی هفتگی شرکای همکاری در آن کشور.',
   tabs:[['list','فرصت‌ها'],['glance','شرایط شرکت در مناقصه در یک نگاه'],['partners','شرکای کشورهای ستاره‌دار']], intl:'پذیرش شرکت‌های بین‌المللی'},
 web:{note:'درخواست‌های طراحی سایت و سئو از همه‌ی منابع داخلی و بین‌المللی. پیشنهاد پیش‌فرض برای مشتریان داخلی: طراحی سایت + سئو.',
   tabs:[['list','فرصت‌ها'],['glance','شرایط در یک نگاه']], intl:'پذیرش شرکت‌های خارجی / داخلی'},
 investors:{note:'صندوق‌های خطرپذیر، سرمایه‌گذاران شرکتی و شتاب‌دهنده‌های جهان در حوزه‌های هوش مصنوعی شرکت – به‌روزرسانی هفتگی. ارقام از منبع ذکرشده‌اند و ممکن است قدیمی باشند؛ پیش از مذاکره با سایت رسمی تطبیق دهید.',
   tabs:[['all','همه'],['vc','صندوق خطرپذیر'],['cvc','سرمایه‌گذار شرکتی'],['accelerator','شتاب‌دهنده']]},
 events:{note:'رویدادهای هوش مصنوعی و حوزه‌های انرژی، پزشکی، هوانوردی، هسته‌ای و شهری در ایران و جهان – به‌روزرسانی روزانه.',
   tabs:[['iran','ایران'],['world','جهان'],['all','همه']]}};
let page='international', tab='list';
try{const s=JSON.parse(localStorage.getItem('scb-view')||'{}');if(PAGES[s.page]){page=s.page;tab=s.tab}}catch(e){}
document.getElementById('last').textContent=DATA.last_run||'—';
document.getElementById('stars').textContent=DATA.starred.length?DATA.starred.join('، '):'هنوز کشوری انتخاب نشده';
const sel=document.getElementById('st');
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function li(a){return a&&a.length?'<ul>'+a.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':''}
function link(u,t){return u?`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t||u)}</a>`:''}
function starBtn(c){if(!c)return '';const on=STARRED.has(c.toLowerCase());
  return `<button class="star" title="${on?'ستاره‌دار':'ستاره‌دار کردن'}" onclick="starHelp('${esc(c)}')">${on?'★':'☆'}</button>`}
function starHelp(c){alert('برای ستاره‌دار کردن «'+c+'»:\n۱) در GitHub فایل config.json را باز کنید و نام کشور را به starred_countries اضافه کنید\nیا ۲) دستور زیر را اجرا کنید:\npython -m agent star "'+c+'"\nاز اجرای بعدی، شرکت‌های همکار در این کشور جست‌وجو و پیش‌نویس ایمیل در وب‌میل ساخته می‌شود.')}
function inPage(t){if(page==='web')return t.line==='web';return (t.line||'ai')==='ai'&&(t.market||'international')===page}
function cond(t){const f=t.facts||{}, c=(t.analysis||{}).conditions||{};
  return {price:c.price_fa||f.price||'—',guarantee:c.guarantee_fa||f.guarantee||'—',experience:c.experience_fa||f.experience||'—',international:c.international_fa||f.international||'—'}}
function deadline(t){const d=t.days_left==null?'نامشخص':(t.days_left<=7?`<span class="urgent">${t.days_left} روز</span>`:t.days_left+' روز');
  return `${esc(t.deadline_fa||t.deadline||'؟')} (${d})`}
function q(){return document.getElementById('q').value.trim().toLowerCase()}
function setStatusOptions(map,withActive){sel.innerHTML=(withActive?'<option value="active">همه فعال‌ها</option>':'')+'<option value="">همه</option>'+
  Object.entries(map).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}
function tenders(){const s=sel.value,qq=q();return DATA.tenders.filter(t=>inPage(t)&&(s==='active'?ACTIVE.has(t.status):!s||t.status===s)&&
  (!qq||[t.title,t.country,t.buyer,t.source,t.sector].join(' ').toLowerCase().includes(qq)))}
function kpis(){let items;
 if(page==='investors'){const v=DATA.investors,c=t=>v.filter(x=>x.type===t).length;items=[['کل',v.length],['صندوق خطرپذیر',c('vc')],['سرمایه‌گذار شرکتی',c('cvc')],['شتاب‌دهنده',c('accelerator')],['در حال مذاکره',v.filter(x=>['contacted','meeting','due_diligence','term_sheet'].includes(x.status)).length]]}
 else if(page==='events'){const e=DATA.events;items=[['رویداد پیش رو',e.length],['ایران',e.filter(x=>x.region==='iran').length],['جهان',e.filter(x=>x.region==='world').length],
   ['تاریخ اعلام نشده',e.filter(x=>x.date_status==='tba').length],['در حال بررسی',e.filter(x=>x.status==='considering').length],['ثبت‌نام شد',e.filter(x=>['registered','attending'].includes(x.status)).length]]}
 else{const t=DATA.tenders.filter(inPage),c=s=>t.filter(x=>x.status===s).length;
  items=[['فعال',t.filter(x=>ACTIVE.has(x.status)).length],['جدید',c('new')],['در جست‌وجوی شریک',c('partner_search')+c('mou_negotiation')],
  ['آماده‌سازی پیشنهاد',c('bid_prep')+c('proposal_drafting')],['ارسال شده',c('submitted')],['مهلت ≤ ۷ روز',t.filter(x=>ACTIVE.has(x.status)&&x.days_left!=null&&x.days_left<=7).length]];
  if(page==='international')items.push(['پیش‌نویس همکاری',DATA.partners.length])}
 document.getElementById('kpis').innerHTML=items.map(([l,v])=>`<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join('')}
function card(t){const a=t.analysis||{},k=cond(t),intl=PAGES[page].intl;
  const files=Object.values(t.files||{}).map(v=>`<code>${esc(v)}</code>`).join(' ');
  const partnersHtml=(t.partners||[]).map(p=>`<li>${esc(p.name)} – ${link(p.website)} – ${esc(p.why_fa)}</li>`).join('');
  const offer=t.line==='web'?`<div class="offer">پیشنهاد خدمت: طراحی سایت${t.market==='domestic'?' + سئو (بهینه‌سازی موتور جست‌وجو)':' + سئو'}</div>`:'';
  return `<div class="card"><div class="top"><div><div class="title">${esc(t.title)}</div>
  <div class="meta">${page!=='domestic'?starBtn(t.country):''}${esc(t.country)} · ${esc(t.buyer)} · ${esc(t.source)} · مهلت ${deadline(t)}${a.relevance_score!=null?' · امتیاز '+a.relevance_score:''}</div></div>
  <div><span class="pill sector">${esc(t.sector||'نامشخص')}</span> <span class="pill s-${t.status}">${esc(ST[t.status])}</span></div></div>
  ${offer}
  <div class="glance"><div><b>قیمت</b>${esc(k.price)}</div><div><b>ضمانت‌نامه</b>${esc(k.guarantee)}</div>
  <div><b>رزومه، رفرنس و نمونه‌کار</b>${esc(k.experience)}</div><div><b>${intl}</b>${esc(k.international)}</div></div>
  <details><summary>جزئیات و اقدامات</summary>
  ${a.summary_fa?'<p>'+esc(a.summary_fa)+'</p>':'<p class="meta">تحلیل هوشمند نشده – امتیاز کلیدواژه '+esc(t.keyword_score)+'</p>'}
  ${a.eligibility_reasoning_fa?'<b>امکان شرکت:</b> '+esc(a.eligibility_reasoning_fa):''}
  ${a.key_requirements_fa?'<div><b>الزامات کلیدی:</b>'+li(a.key_requirements_fa)+'</div>':''}
  ${a.compliance_flags_fa&&a.compliance_flags_fa.length?'<div><b>⚠️ ملاحظات انطباق:</b>'+li(a.compliance_flags_fa)+'</div>':''}
  ${partnersHtml?'<div><b>شرکای پیشنهادی:</b><ul>'+partnersHtml+'</ul></div>':''}
  ${a.next_actions_fa?'<div><b>گام‌های بعدی:</b>'+li(a.next_actions_fa)+'</div>':''}
  ${files?'<div><b>فایل‌ها:</b> '+files+(t.draft_saved_to?' · پیش‌نویس: '+esc(t.draft_saved_to):'')+'</div>':''}
  <div>${link(t.url,'مشاهده آگهی اصلی')}${t.setad_number?' · شماره معامله ستاد <code>'+esc(t.setad_number)+'</code>':''} · شناسه <code>${esc(t.id)}</code></div>
  </details></div>`}
function glance(list){if(!list.length)return '<p class="empty">موردی یافت نشد.</p>';const intl=PAGES[page].intl;
  return `<div class="tablewrap"><table><thead><tr><th>عنوان</th><th>کشور مبدأ / خریدار</th><th>بخش</th><th>مهلت</th>
  <th>قیمت پیشنهادی / برآورد</th><th>شرایط ضمانت‌نامه</th><th>رزومه، رفرنس و نمونه‌کار</th><th>${intl}</th><th>وضعیت</th></tr></thead><tbody>`+
  list.map(t=>{const k=cond(t);return `<tr><td class="t">${link(t.url,t.title)}</td>
  <td data-l="کشور مبدأ / خریدار">${esc(t.country)}<br><span class="meta">${esc(t.buyer)}</span></td><td data-l="بخش">${esc(t.sector||'نامشخص')}</td>
  <td data-l="مهلت">${deadline(t)}</td><td data-l="قیمت">${esc(k.price)}</td><td data-l="ضمانت‌نامه">${esc(k.guarantee)}</td>
  <td data-l="رزومه و رفرنس">${esc(k.experience)}</td><td data-l="${intl}">${esc(k.international)}</td>
  <td data-l="وضعیت"><span class="pill s-${t.status}">${esc(ST[t.status])}</span></td></tr>`}).join('')+'</tbody></table></div>'}
function partnersView(){const s=sel.value,qq=q();
  const list=DATA.partners.filter(p=>(!s||p.status===s)&&(!qq||[p.name,p.country,p.sector_fa,p.fit_fa].join(' ').toLowerCase().includes(qq)));
  if(!DATA.starred.length)return '<p class="empty">هنوز کشوری ستاره‌دار نشده است. روی ☆ کنار نام کشور در تب «فرصت‌ها» بزنید تا روش انتخاب را ببینید.</p>';
  if(!list.length)return '<p class="empty">شرکای کشورهای ستاره‌دار در اجرای بعدی (نیازمند کلید Claude) جست‌وجو می‌شوند.</p>';
  return `<div class="tablewrap"><table><thead><tr><th>شرکت</th><th>کشور</th><th>بخش و فعالیت</th><th>چرا مناسب است</th><th>وب‌سایت / لینکدین</th>
  <th>ایمیل گیرنده</th><th>موضوع ایمیل</th><th>وضعیت</th></tr></thead><tbody>`+list.map(p=>`<tr><td class="t">${esc(p.name)}<br><span class="meta">${esc(p.city)}</span></td>
  <td data-l="کشور">${esc(p.country)}</td><td data-l="بخش">${esc(p.sector_fa)}</td><td data-l="تناسب">${esc(p.fit_fa)}</td>
  <td data-l="لینک‌ها">${link(p.website,'وب‌سایت')}${p.linkedin_url?' · '+link(p.linkedin_url,'LinkedIn'):''}</td>
  <td data-l="ایمیل">${p.email?`<code>${esc(p.email)}</code><br>${link(p.email_source,'منبع')}`:'<span class="meta">ایمیل عمومی پیدا نشد – از فرم سایت</span>'}</td>
  <td data-l="موضوع">${esc(p.subject)}<br><span class="meta">${esc(p.draft_saved_to||'')}</span></td>
  <td data-l="وضعیت"><span class="pill s-${p.status}">${esc(DATA.partner_statuses[p.status]||p.status)}</span></td></tr>`).join('')+'</tbody></table></div>'}
function investorsView(){const s=sel.value,qq=q();
  const list=DATA.investors.filter(v=>(tab==='all'||v.type===tab)&&(!s||v.status===s)&&
   (!qq||[v.name,v.hq,v.focus_fa,v.stage_fa,(v.domains||[]).map(x=>DATA.labels[x]||x).join(' ')].join(' ').toLowerCase().includes(qq)));
  if(!list.length)return '<p class="empty">موردی یافت نشد.</p>';
  return `<div class="tablewrap"><table><thead><tr><th>سرمایه‌گذار</th><th>مقر</th><th>حوزه‌های ما</th><th>مرحله و مبلغ</th><th>اندازه‌ی صندوق / بودجه</th>
  <th>سرمایه‌گذاری‌های انجام‌شده</th><th>حوزه‌ی علاقه‌مندی</th><th>راه ارتباط</th><th>ملاحظات</th><th>وضعیت</th></tr></thead><tbody>`+
  list.map(v=>`<tr><td class="t">${esc(v.name)}<br><span class="meta">${esc(DATA.investor_types[v.type]||v.type)}</span></td>
  <td data-l="مقر">${esc(v.hq)}</td><td data-l="حوزه">${esc((v.domains||[]).map(x=>DATA.labels[x]||x).join('، '))}</td>
  <td data-l="مرحله و مبلغ">${esc(v.stage_fa)}<br><span class="meta">${esc(v.ticket_fa)}</span></td><td data-l="اندازه صندوق">${esc(v.fund_fa)}</td>
  <td data-l="سرمایه‌گذاری‌ها">${esc(v.investments_fa)}</td><td data-l="علاقه‌مندی">${esc(v.focus_fa)}</td>
  <td data-l="ارتباط">${link(v.website,'وب‌سایت')}${v.apply&&v.apply!==v.website?'<br>'+link(v.apply,'ارائه‌ی طرح / ثبت‌نام'):''}${v.email?'<br><code>'+esc(v.email)+'</code>':''}<br>${link(v.source,'منبع ارقام')}</td>
  <td data-l="ملاحظات">${esc(v.compliance_fa||'—')}</td>
  <td data-l="وضعیت"><span class="pill s-${v.status}">${esc(DATA.investor_statuses[v.status]||v.status)}</span><br><code>${esc(v.id)}</code></td></tr>`).join('')+'</tbody></table></div>'}
function eventsView(){const s=sel.value,qq=q();
  const list=DATA.events.filter(e=>(tab==='all'||e.region===tab)&&(!s||e.status===s)&&(!qq||[e.name,e.name_fa,e.city,e.country,e.type].join(' ').toLowerCase().includes(qq)));
  if(!list.length)return '<p class="empty">رویدادی یافت نشد.</p>';
  return `<div class="tablewrap"><table><thead><tr><th>رویداد</th><th>محل</th><th>تاریخ</th><th>حوزه</th><th>نوع</th><th>چرا مهم است</th><th>نحوه‌ی مشارکت</th><th>وضعیت</th></tr></thead><tbody>`+
  list.map(e=>{const date=e.start?(e.start+(e.end&&e.end!==e.start?' تا '+e.end:'')+(e.date_status==='to_verify'?' <span class="meta">(نیاز به تأیید)</span>':'')):'<span class="meta">اعلام نشده – '+esc(e.usual_period_fa||'')+'</span>';
   return `<tr><td class="t">${link(e.url,e.name_fa||e.name)}<br><span class="meta">${esc(e.name)}</span></td><td data-l="محل">${esc(e.city)}، ${esc(e.country)}</td>
   <td data-l="تاریخ">${date}${e.source?'<br>'+link(e.source,'منبع تاریخ'):''}</td><td data-l="حوزه">${esc((e.categories||[]).map(x=>DATA.labels[x]||x).join('، '))}</td>
   <td data-l="نوع">${esc(e.type)}</td><td data-l="اهمیت">${esc(e.why_fa)}</td><td data-l="مشارکت">${esc(e.participation_fa)}</td>
   <td data-l="وضعیت"><span class="pill s-${e.status}">${esc(DATA.event_statuses[e.status]||e.status)}</span><br><code>${esc(e.id)}</code></td></tr>`}).join('')+'</tbody></table></div>'}
function render(){
  if(!PAGES[page].tabs.some(([k])=>k===tab))tab=PAGES[page].tabs[0][0];
  document.querySelectorAll('.pages button').forEach(b=>b.setAttribute('aria-selected',b.dataset.page===page));
  document.getElementById('tabs').innerHTML=PAGES[page].tabs.map(([k,l])=>`<button role="tab" data-tab="${k}" aria-selected="${k===tab}">${l}</button>`).join('');
  document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;sel.value='';render()});
  document.getElementById('srcnote').textContent=PAGES[page].note;
  const prev=sel.value;
  if(page==='events')setStatusOptions(DATA.event_statuses,false);
  else if(page==='investors')setStatusOptions(DATA.investor_statuses,false);
  else if(tab==='partners')setStatusOptions(DATA.partner_statuses,false);
  else setStatusOptions(ST,true);
  if([...sel.options].some(o=>o.value===prev))sel.value=prev;
  kpis();
  const v=document.getElementById('view');
  if(page==='events')v.innerHTML=eventsView();
  else if(page==='investors')v.innerHTML=investorsView();
  else if(tab==='partners')v.innerHTML=partnersView();
  else{const list=tenders();v.innerHTML=tab==='glance'?glance(list):(list.map(card).join('')||'<p class="empty">موردی یافت نشد.</p>')}
  try{localStorage.setItem('scb-view',JSON.stringify({page,tab}))}catch(e){}}
document.querySelectorAll('.pages button').forEach(b=>b.onclick=()=>{page=b.dataset.page;tab=PAGES[page].tabs[0][0];sel.value='';render()});
document.getElementById('q').oninput=render; sel.onchange=render; render();
</script>
</body></html>
"""


def render(cfg, state, run_info=None):
    order = list(store.STATUSES)
    tenders = sorted(state["tenders"].values(),
                     key=lambda t: (order.index(t["status"]) if t["status"] != "new" else 1.5,
                                    t.get("days_left") if t.get("days_left") is not None else 999))
    keep = ("id", "title", "country", "buyer", "source", "market", "line", "sector", "deadline", "deadline_fa",
            "days_left", "url", "status", "keyword_score", "domains", "analysis", "partners", "files",
            "draft_saved_to", "facts", "setad_number")
    ev = sorted((e for e in events.load()["events"].values() if events.is_upcoming(e)),
                key=lambda e: (e.get("start") or "9999", e.get("name", "")))
    pt = sorted(partners.load()["companies"].values(), key=lambda p: (p["country"], p["name"]))
    data = {"labels": cfg.get("domain_labels_fa", {}), "statuses": store.STATUSES, "active": sorted(store.ACTIVE),
            "tenders": [{k: t.get(k) for k in keep} for t in tenders],
            "events": ev, "event_statuses": events.STATUSES,
            "partners": pt, "partner_statuses": partners.STATUSES,
            "investors": sorted(investors.load()["investors"].values(), key=lambda v: (v["type"], v["name"])),
            "investor_statuses": investors.STATUSES, "investor_types": investors.TYPES,
            "starred": cfg.get("starred_countries", []),
            "last_run": (run_info or {}).get("at") or (state.get("runs") or [{}])[-1].get("at")}
    out = ROOT / cfg["dashboard"]["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    return out
