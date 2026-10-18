"""Static Persian (RTL) dashboard written to docs/index.html - can be served by GitHub Pages or opened locally."""
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
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2430;--muted:#5d6878;--line:#e3e7ec;--accent:#0f6e6e;
--new:#3b6fd8;--partner:#b26b00;--direct:#1f8a4c;--skip:#8a94a3;--warn:#c0392b}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11161d;--card:#18202a;--ink:#e6ebf1;
--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;--skip:#76808e;--warn:#ef7b6e}}
:root[data-theme="dark"]{--bg:#11161d;--card:#18202a;--ink:#e6ebf1;--muted:#9aa6b5;--line:#2a3441;--accent:#4fb8b8;
--new:#7aa2f0;--partner:#e0a34a;--direct:#5cc58a;--skip:#76808e;--warn:#ef7b6e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 Vazirmatn,Tahoma,sans-serif}
header{padding:20px 16px 8px;max-width:1100px;margin:auto}h1{margin:0;font-size:22px}
.sub{color:var(--muted);font-size:13px}main{max-width:1100px;margin:auto;padding:0 16px 40px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0}
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
</style>
</head>
<body>
<header><h1>توسعه بازار برون مرزی هوشمند</h1>
<div class="sub">آخرین اجرا: <span id="last"></span> · منابع: TED (اتحادیه اروپا)، بانک جهانی، Find a Tender (بریتانیا)</div></header>
<main>
<div class="kpis" id="kpis"></div>
<div class="bar"><input id="q" placeholder="جست‌وجو در عنوان، کشور، خریدار…">
<select id="st"><option value="active">همه فعال‌ها</option><option value="">همه</option></select></div>
<div id="list"></div>
</main>
<script>
const DATA = __DATA__;
const ST = DATA.statuses, ACTIVE = new Set(DATA.active);
document.getElementById('last').textContent = DATA.last_run || '—';
const sel = document.getElementById('st');
Object.entries(ST).forEach(([k,v])=>{const o=document.createElement('option');o.value=k;o.textContent=v;sel.appendChild(o)});
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function li(a){return a&&a.length?'<ul>'+a.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':''}
function kpis(){const t=DATA.tenders, c=s=>t.filter(x=>x.status===s).length;
 const items=[['فعال',t.filter(x=>ACTIVE.has(x.status)).length],['جدید',c('new')],['در جست‌وجوی شریک',c('partner_search')+c('mou_negotiation')],
 ['آماده‌سازی پیشنهاد',c('bid_prep')+c('proposal_drafting')],['ارسال شده',c('submitted')],['مهلت ≤ ۷ روز',t.filter(x=>ACTIVE.has(x.status)&&x.days_left!=null&&x.days_left<=7).length]];
 document.getElementById('kpis').innerHTML=items.map(([l,v])=>`<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join('')}
function render(){const q=document.getElementById('q').value.trim().toLowerCase(), s=sel.value;
 const rows=DATA.tenders.filter(t=>(s==='active'?ACTIVE.has(t.status):!s||t.status===s)&&
  (!q||[t.title,t.country,t.buyer,t.source].join(' ').toLowerCase().includes(q)));
 document.getElementById('list').innerHTML=rows.map(t=>{const a=t.analysis||{};
  const dl=t.days_left==null?'نامشخص':(t.days_left<=7?`<span class="urgent">${t.days_left} روز</span>`:t.days_left+' روز');
  const files=Object.entries(t.files||{}).map(([k,v])=>`<code>${esc(v)}</code>`).join(' ');
  const partners=(t.partners||[]).map(p=>`<li>${esc(p.name)} – <a href="${esc(p.website)}" target="_blank" rel="noopener">${esc(p.website)}</a> – ${esc(p.why_fa)}</li>`).join('');
  return `<div class="card"><div class="top"><div><div class="title">${esc(t.title)}</div>
  <div class="meta">${esc(t.country)} · ${esc(t.buyer)} · ${esc(t.source)} · مهلت ${esc(t.deadline||'؟')} (${dl})${a.relevance_score!=null?' · امتیاز '+a.relevance_score:''}</div></div>
  <span class="pill s-${t.status}">${esc(ST[t.status])}</span></div>
  <details><summary>جزئیات و اقدامات</summary>
  ${a.summary_fa?'<p>'+esc(a.summary_fa)+'</p>':'<p class="meta">هنوز تحلیل نشده – امتیاز کلیدواژه '+esc(t.keyword_score)+' ('+esc((t.domains||[]).join('، '))+')</p>'}
  ${a.eligibility_reasoning_fa?'<b>امکان شرکت:</b> '+esc(a.eligibility_reasoning_fa):''}
  ${a.key_requirements_fa?'<div><b>الزامات کلیدی:</b>'+li(a.key_requirements_fa)+'</div>':''}
  ${a.compliance_flags_fa&&a.compliance_flags_fa.length?'<div><b>⚠️ ملاحظات انطباق:</b>'+li(a.compliance_flags_fa)+'</div>':''}
  ${partners?'<div><b>شرکای پیشنهادی:</b><ul>'+partners+'</ul></div>':''}
  ${a.next_actions_fa?'<div><b>گام‌های بعدی:</b>'+li(a.next_actions_fa)+'</div>':''}
  ${files?'<div><b>فایل‌ها:</b> '+files+(t.draft_saved_to?' · پیش‌نویس: '+esc(t.draft_saved_to):'')+'</div>':''}
  <div><a href="${esc(t.url)}" target="_blank" rel="noopener">مشاهده آگهی اصلی</a> · شناسه <code>${esc(t.id)}</code></div>
  </details></div>`}).join('')||'<p class="meta">موردی یافت نشد.</p>'}
document.getElementById('q').oninput=render; sel.onchange=render; kpis(); render();
</script>
</body></html>
"""


def render(cfg, state, run_info=None):
    order = list(store.STATUSES)
    tenders = sorted(state["tenders"].values(),
                     key=lambda t: (order.index(t["status"]) if t["status"] != "new" else 1.5,
                                    t.get("days_left") if t.get("days_left") is not None else 999))
    slim = [{k: t.get(k) for k in ("id", "title", "country", "buyer", "source", "deadline", "days_left", "url", "status",
                                    "keyword_score", "domains", "analysis", "partners", "files", "draft_saved_to")}
            for t in tenders]
    data = {"statuses": store.STATUSES, "active": sorted(store.ACTIVE), "tenders": slim,
            "last_run": (run_info or {}).get("at") or (state.get("runs") or [{}])[-1].get("at")}
    out = ROOT / cfg["dashboard"]["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    return out
