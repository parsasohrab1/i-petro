"""Static Persian (RTL) dashboard written to docs/index.html.

Two pages - domestic market (Iran) and international market - each with two tabs:
opportunities (cards with analysis and next steps) and bid conditions at a glance
(price, guarantee, references/experience, acceptance of international firms).
"""
import json

from . import store
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
--new:#3b6fd8;--partner:#b26b00;--direct:#1f8a4c;--skip:#8a94a3;--warn:#c0392b;--head:#eef1f4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11161d;--card:#18202a;--ink:#e6ebf1;
--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;--accent-ink:#0b1116;--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;
--skip:#76808e;--warn:#ef7b6e;--head:#1f2833}}
:root[data-theme="dark"]{--bg:#11161d;--card:#18202a;--ink:#e6ebf1;--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;
--accent-ink:#0b1116;--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;--skip:#76808e;--warn:#ef7b6e;--head:#1f2833}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 Vazirmatn,Tahoma,sans-serif}
header,main{max-width:1200px;margin:auto;padding:0 16px}header{padding-top:18px}
h1{margin:0;font-size:22px}.sub{color:var(--muted);font-size:13px}
.pages{display:flex;gap:8px;margin:14px 0 4px;flex-wrap:wrap}
.pages button,.tabs button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);
border-radius:10px;padding:8px 16px}
.pages button{font-weight:600;font-size:16px}
.pages button[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tabs{display:flex;gap:6px;margin:10px 0;flex-wrap:wrap}
.tabs button{padding:5px 12px;font-size:14px}
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
.pill{font-size:12px;padding:2px 9px;border-radius:99px;border:1px solid currentColor;white-space:nowrap}
.s-new{color:var(--new)}.s-partner_search,.s-mou_negotiation{color:var(--partner)}
.s-bid_prep,.s-proposal_drafting,.s-submitted,.s-won{color:var(--direct)}.s-skipped,.s-expired,.s-lost{color:var(--skip)}
.urgent{color:var(--warn);font-weight:600}details{margin-top:6px}summary{cursor:pointer;color:var(--accent)}
ul{margin:4px 0;padding-inline-start:20px}a{color:var(--accent)}
code{font-size:12px;background:var(--bg);padding:1px 5px;border-radius:5px;direction:ltr;display:inline-block}
.glance{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin:8px 0}
.glance div{border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:13px}
.glance b{display:block;color:var(--muted);font-size:12px;font-weight:600}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:980px;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th{background:var(--head);font-weight:600;position:sticky;top:0}
td.t{min-width:220px;font-weight:600}.empty{color:var(--muted);padding:20px}
.note{color:var(--muted);font-size:12px;margin:6px 0}
@media (max-width:900px){table{min-width:0}thead{display:none}tr{display:block;border-bottom:1px solid var(--line);padding:8px 0}
td{display:block;border:0;padding:3px 12px}td.t{min-width:0}td[data-l]::before{content:attr(data-l) ": ";color:var(--muted);font-weight:600}}
</style>
</head>
<body>
<header><h1>توسعه بازار برون مرزی هوشمند</h1>
<div class="sub">آخرین اجرا: <span id="last"></span></div>
<nav class="pages" role="tablist">
<button role="tab" data-page="domestic">بازار داخلی (ایران)</button>
<button role="tab" data-page="international">بازار بین‌المللی</button>
</nav></header>
<main>
<div class="note" id="srcnote"></div>
<div class="kpis" id="kpis"></div>
<div class="tabs" role="tablist">
<button role="tab" data-tab="list">فرصت‌ها</button>
<button role="tab" data-tab="glance">شرایط شرکت در مناقصه در یک نگاه</button>
</div>
<div class="bar"><input id="q" placeholder="جست‌وجو در عنوان، کشور، خریدار…">
<select id="st"><option value="active">همه فعال‌ها</option><option value="">همه</option></select></div>
<div id="view"></div>
</main>
<script>
const DATA = __DATA__;
const ST = DATA.statuses, ACTIVE = new Set(DATA.active);
const SRC = {domestic:'منبع: سامانه تدارکات الکترونیکی دولت (ستاد). تحلیل از روی داده‌ی عمومی آگهی؛ جزئیات تضمین و ارزیابی در اسناد ستاد.',
  international:'منابع: TED (اتحادیه اروپا)، بانک جهانی، Find a Tender (بریتانیا). شرایط پس از تحلیل از متن کامل آگهی استخراج می‌شود.'};
const INTL_LABEL = {domestic:'شرایط پذیرش شرکت‌ها', international:'پذیرش شرکت‌های بین‌المللی'};
let page='international', tab='list';
try{const s=JSON.parse(localStorage.getItem('scb-view')||'{}');page=s.page||page;tab=s.tab||tab}catch(e){}
document.getElementById('last').textContent = DATA.last_run || '—';
const sel=document.getElementById('st');
Object.entries(ST).forEach(([k,v])=>{const o=document.createElement('option');o.value=k;o.textContent=v;sel.appendChild(o)});
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function li(a){return a&&a.length?'<ul>'+a.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':''}
function cond(t){const f=t.facts||{}, c=(t.analysis||{}).conditions||{};
  return {price:c.price_fa||f.price||'—',guarantee:c.guarantee_fa||f.guarantee||'—',
          experience:c.experience_fa||f.experience||'—',international:c.international_fa||f.international||'—'}}
function deadline(t){const d=t.days_left==null?'نامشخص':(t.days_left<=7?`<span class="urgent">${t.days_left} روز</span>`:t.days_left+' روز');
  return `${esc(t.deadline_fa||t.deadline||'؟')} (${d})`}
function rows(){const q=document.getElementById('q').value.trim().toLowerCase(), s=sel.value;
  return DATA.tenders.filter(t=>(t.market||'international')===page&&(s==='active'?ACTIVE.has(t.status):!s||t.status===s)&&
   (!q||[t.title,t.country,t.buyer,t.source].join(' ').toLowerCase().includes(q)))}
function kpis(){const t=DATA.tenders.filter(x=>(x.market||'international')===page), c=s=>t.filter(x=>x.status===s).length;
 const items=[['فعال',t.filter(x=>ACTIVE.has(x.status)).length],['جدید',c('new')],['در جست‌وجوی شریک',c('partner_search')+c('mou_negotiation')],
 ['آماده‌سازی پیشنهاد',c('bid_prep')+c('proposal_drafting')],['ارسال شده',c('submitted')],['مهلت ≤ ۷ روز',t.filter(x=>ACTIVE.has(x.status)&&x.days_left!=null&&x.days_left<=7).length]];
 document.getElementById('kpis').innerHTML=items.map(([l,v])=>`<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join('')}
function card(t){const a=t.analysis||{}, k=cond(t);
  const files=Object.values(t.files||{}).map(v=>`<code>${esc(v)}</code>`).join(' ');
  const partners=(t.partners||[]).map(p=>`<li>${esc(p.name)} – <a href="${esc(p.website)}" target="_blank" rel="noopener">${esc(p.website)}</a> – ${esc(p.why_fa)}</li>`).join('');
  return `<div class="card"><div class="top"><div><div class="title">${esc(t.title)}</div>
  <div class="meta">${esc(t.country)} · ${esc(t.buyer)} · ${esc(t.source)} · مهلت ${deadline(t)}${a.relevance_score!=null?' · امتیاز '+a.relevance_score:''}</div></div>
  <span class="pill s-${t.status}">${esc(ST[t.status])}</span></div>
  <div class="glance"><div><b>قیمت</b>${esc(k.price)}</div><div><b>ضمانت‌نامه</b>${esc(k.guarantee)}</div>
  <div><b>رزومه، رفرنس و نمونه‌کار</b>${esc(k.experience)}</div><div><b>${INTL_LABEL[page]}</b>${esc(k.international)}</div></div>
  <details><summary>جزئیات و اقدامات</summary>
  ${a.summary_fa?'<p>'+esc(a.summary_fa)+'</p>':'<p class="meta">تحلیل هوشمند نشده – امتیاز کلیدواژه '+esc(t.keyword_score)+' ('+esc((t.domains||[]).map(x=>DATA.labels[x]||x).join('، '))+')</p>'}
  ${a.eligibility_reasoning_fa?'<b>امکان شرکت:</b> '+esc(a.eligibility_reasoning_fa):''}
  ${a.key_requirements_fa?'<div><b>الزامات کلیدی:</b>'+li(a.key_requirements_fa)+'</div>':''}
  ${a.compliance_flags_fa&&a.compliance_flags_fa.length?'<div><b>⚠️ ملاحظات انطباق:</b>'+li(a.compliance_flags_fa)+'</div>':''}
  ${partners?'<div><b>شرکای پیشنهادی:</b><ul>'+partners+'</ul></div>':''}
  ${a.next_actions_fa?'<div><b>گام‌های بعدی:</b>'+li(a.next_actions_fa)+'</div>':''}
  ${files?'<div><b>فایل‌ها:</b> '+files+(t.draft_saved_to?' · پیش‌نویس: '+esc(t.draft_saved_to):'')+'</div>':''}
  <div><a href="${esc(t.url)}" target="_blank" rel="noopener">مشاهده آگهی اصلی</a>${t.setad_number?' · شماره معامله ستاد <code>'+esc(t.setad_number)+'</code>':''} · شناسه <code>${esc(t.id)}</code></div>
  </details></div>`}
function glance(list){if(!list.length)return '<p class="empty">موردی یافت نشد.</p>';
  return `<div class="tablewrap"><table><thead><tr><th>عنوان</th><th>${page==='domestic'?'استان / دستگاه':'کشور / خریدار'}</th><th>مهلت</th>
  <th>قیمت پیشنهادی / برآورد</th><th>شرایط ضمانت‌نامه</th><th>رزومه، رفرنس و نمونه‌کار</th><th>${INTL_LABEL[page]}</th><th>وضعیت</th></tr></thead><tbody>`+
  list.map(t=>{const k=cond(t);return `<tr><td class="t"><a href="${esc(t.url)}" target="_blank" rel="noopener">${esc(t.title)}</a></td>
  <td data-l="${page==='domestic'?'استان / دستگاه':'کشور / خریدار'}">${esc(t.country)}<br><span class="meta">${esc(t.buyer)}</span></td>
  <td data-l="مهلت">${deadline(t)}</td><td data-l="قیمت">${esc(k.price)}</td><td data-l="ضمانت‌نامه">${esc(k.guarantee)}</td>
  <td data-l="رزومه و رفرنس">${esc(k.experience)}</td><td data-l="${INTL_LABEL[page]}">${esc(k.international)}</td>
  <td data-l="وضعیت"><span class="pill s-${t.status}">${esc(ST[t.status])}</span></td></tr>`}).join('')+'</tbody></table></div>'}
function render(){
  document.querySelectorAll('.pages button').forEach(b=>b.setAttribute('aria-selected',b.dataset.page===page));
  document.querySelectorAll('.tabs button').forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===tab));
  document.getElementById('srcnote').textContent=SRC[page];
  kpis(); const list=rows();
  document.getElementById('view').innerHTML = tab==='glance'?glance(list):(list.map(card).join('')||'<p class="empty">موردی یافت نشد.</p>');
  try{localStorage.setItem('scb-view',JSON.stringify({page,tab}))}catch(e){}}
document.querySelectorAll('.pages button').forEach(b=>b.onclick=()=>{page=b.dataset.page;render()});
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;render()});
document.getElementById('q').oninput=render; sel.onchange=render; render();
</script>
</body></html>
"""


def render(cfg, state, run_info=None):
    order = list(store.STATUSES)
    tenders = sorted(state["tenders"].values(),
                     key=lambda t: (order.index(t["status"]) if t["status"] != "new" else 1.5,
                                    t.get("days_left") if t.get("days_left") is not None else 999))
    keep = ("id", "title", "country", "buyer", "source", "market", "deadline", "deadline_fa", "days_left", "url",
            "status", "keyword_score", "domains", "analysis", "partners", "files", "draft_saved_to", "facts",
            "setad_number")
    slim = [{k: t.get(k) for k in keep} for t in tenders]
    data = {"labels": cfg.get("domain_labels_fa", {}), "statuses": store.STATUSES, "active": sorted(store.ACTIVE),
            "tenders": slim,
            "last_run": (run_info or {}).get("at") or (state.get("runs") or [{}])[-1].get("at")}
    out = ROOT / cfg["dashboard"]["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    return out
