"""Adds automatic call-for-papers (CFP) venues to the Articles tab of platform/index.html.

The calls are written by the weekly CFP job to the database document settings/article_calls  ({map: {id: venue}})
and are merged into the venue list; admins get an in-page notification for every call that no product fits.
python docs/abstracts/patch_calls.py platform/index.html platform/index.html
"""
import sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()


def once(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)


once('  S.db.doc("settings/article_product").onSnapshot(',
     '  S.db.doc("settings/article_calls").onSnapshot(d => { S.calls = d.exists ? (d.data().map||{}) : {}; render(); paintBell(); }, ()=>{});   // {venueId: {…venue fields, found, product_hint, ack}} written by the weekly CFP job\n'
     '  S.db.doc("settings/article_product").onSnapshot(')
once('const artAll = () => [...ARTICLES_SEED, ...S.arts.map(a=>({...a,mine:true}))];',
     'const callsList = () => { const seed=new Set(ARTICLES_SEED.map(x=>x.id)); return Object.values(S.calls||{}).filter(c=>c&&c.id&&c.name&&!seed.has(c.id)).map(c=>({present:"unknown",ver:false,field:"ai_industry",type:"conf",...c,call:true})); };\n'
     'const callNoProduct = c => c.no_product===true || (c.product_hint==null && apBestFor(c).all.length===0);\n'
     'const callIsNew = c => c.found && dayDiff(c.found) >= -21;\n'
     'const artAll = () => [...ARTICLES_SEED, ...callsList(), ...S.arts.map(a=>({...a,mine:true}))];')
once('${a.mine?\' <span class="pill p-info">افزوده‌ی تیم</span>\':""}`,"t")}',
     '${a.mine?\' <span class="pill p-info">افزوده‌ی تیم</span>\':""}${a.call&&callIsNew(a)?\' <span class="pill p-info">فراخوان جدید</span>\':""}${a.call&&callNoProduct(a)?\' <span class="pill p-bad" title="محصول مناسب برای این فراخوان تعریف نشده است">محصول ندارد</span>\':""}`,"t")}')
once("  { const mm=myMember(); if(needsNda(mm)&&!ndaSigned(mm))",
     "  if(isAdmin()) for(const c of callsList()) if(!c.ack && artOpen(c) && callNoProduct(c)) items.push({id:\"cfp\"+c.id,sticky:true,text:`فراخوان جدید «${c.name}»${c.deadline?` (ددلاین ${c.deadline})`:\"\"} محصول مرتبط ندارد؛ برای تعریف محصول جدید با هم‌فکری اقدام کنید (تب مقالات ← «محصول جدید»).`,task:{}});\n"
     "  { const mm=myMember(); if(needsNda(mm)&&!ndaSigned(mm))")
open(out, "w", encoding="utf-8").write(s)
print("ok", len(s))
