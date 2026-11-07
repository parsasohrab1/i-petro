"""Add the abstract Word download (button per row + ZIP) to a copy of the published iPetro page.

usage: python docs/abstracts/merge_into_live_page.py LIVE_HTML OUT_HTML
Only additive: one data block, three functions, one button in the row actions, one in the toolbar, two handler cases and one sentence in the tour text.
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
live, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
s = live.read_text(encoding="utf-8")
seed = json.load(open(ROOT / "platform/abstracts_seed.json", encoding="utf-8")); seed.pop("_note", None)
blob = json.dumps(seed, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def once(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)

BLOCK = r'''/*ABS-START*/const ABS = ''' + blob + r''';/*ABS-END*/
// Abstract drafts per venue: one Word file each (abstract in the venue's format on page 1, internal submission sheet on page 2).
const ABS_GH = "https://github.com/parsasohrab1/";
const absOf = id => ABS.abstracts[id];
const absWords = t => (String(t).match(/\S+/g)||[]).length;
async function buildAbstractDocx(v,a){
  const pr=ABS.profiles[a.profile], prod=ABS.products[a.product], n=absWords(a.abstract);
  const run=(t,{b=false,i=false,sz=22,color=""}={})=>`<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>${b?"<w:b/>":""}${i?"<w:i/>":""}${color?`<w:color w:val="${color}"/>`:""}<w:sz w:val="${sz}"/></w:rPr><w:t xml:space="preserve">${WX(t)}</w:t></w:r>`;
  const par=(inner,{jc="left",after=120,line=276}={})=>`<w:p><w:pPr><w:spacing w:after="${after}" w:line="${line}" w:lineRule="auto"/><w:jc w:val="${jc}"/></w:pPr>${inner}</w:p>`;
  const cell=(w,inner)=>`<w:tc><w:tcPr><w:tcW w:w="${w}" w:type="dxa"/></w:tcPr>${inner}</w:tc>`;
  const row=(k,val)=>`<w:tr>${cell(2400,par(run(k,{b:true,sz:20}),{after:40}))}${cell(6638,par(run(val,{sz:20}),{after:40}))}</w:tr>`;
  const type={journal:"Journal",special:"Journal special issue",conf:"Conference"}[v.type]||v.type;
  const repo=ABS_GH+prod.repo+(prod.new?"":"/tree/"+ABS.branch);
  const todo="Replace every [bracketed] placeholder with the team's own measured values; add author names; confirm the limits in the venue's author guidelines (they are typical values for the venue family, not copied from the call). Patent rule: do not disclose methods covered by the product's filed claims; a patent-attorney review is not required (owner's decision of 2026-11-07)."+(a.draft_note?" "+a.draft_note:"");
  const rows=[["Venue",v.name],["Type",type],["Deadline",(v.deadline||"not stated")+(v.dl_note?" – "+v.dl_note:"")],["Official page",v.url||""],
    ["Abstract rule ("+pr.label+")",`${pr.rule} Typical length ${pr.min}–${pr.max} words; keywords ${pr.kw}.`],["Length of this abstract",`${n} words (limit ${pr.max})`],
    ["Product",prod.name],["Repository",repo],["Repository status",prod.new?"New repository created for this article.":`Existing product; content for the article is on branch "${ABS.branch}".`],["To do before submitting",todo]];
  const bd=t=>`<w:${t} w:val="single" w:sz="4" w:space="0" w:color="999999"/>`;
  const body=[
    par(run(a.title,{b:true,sz:30}),{jc:"center",after:200}),
    par(run("[Author names]"),{jc:"center",after:40}),
    par(run("[Affiliation – e.g. Parsa International Group, Istanbul, Türkiye]  ·  [Corresponding author e-mail]",{i:true,sz:20}),{jc:"center",after:280}),
    par(run("Abstract",{b:true,sz:24}),{after:80}),
    par(run(a.abstract),{jc:"both",after:160,line:300}),
    par(run(pr.kw_label+": ",{b:true})+run(a.keywords.join("; "),{i:true}),{after:0}),
    `<w:p><w:r><w:br w:type="page"/></w:r></w:p>`,
    par(run("Submission sheet (internal – remove before submitting)",{b:true,sz:24,color:"B00020"}),{after:120}),
    `<w:tbl><w:tblPr><w:tblW w:w="9038" w:type="dxa"/><w:tblBorders>${["top","left","bottom","right","insideH","insideV"].map(bd).join("")}</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="2400"/><w:gridCol w:w="6638"/></w:tblGrid>${rows.map(r=>row(...r)).join("")}</w:tbl>`].join("");
  const doc=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>${body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>`;
  const styles=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>`;
  const ct=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>`;
  const rels=items=>`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${items.map(([id,t,tg])=>`<Relationship Id="${id}" Type="${RELNS}/${t}" Target="${tg}"/>`).join("")}</Relationships>`;
  return zipStore([{name:"[Content_Types].xml",data:ct},{name:"_rels/.rels",data:rels([["rId1","officeDocument","word/document.xml"]])},{name:"word/document.xml",data:doc},{name:"word/styles.xml",data:styles},
    {name:"word/_rels/document.xml.rels",data:rels([["rIdSty","styles","styles.xml"]])}]);
}
const ABS_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const absFile = id => `${id.replace(/^s_/,"")}-abstract.docx`;
async function downloadAbstract(id){
  if(!S.downloads){ toast("دریافت فایل فقط داخل claude.ai فعال است."); return; }
  const v=ARTICLES_SEED.find(x=>x.id===id), a=absOf(id); if(!v||!a) return;
  try{ await S.downloads.save({filename:absFile(id),data:new Blob([await buildAbstractDocx(v,a)],{type:ABS_DOCX})}); }
  catch(err){ if(!err||err.code!=="declined"){ toast("ساخت یا دریافت فایل Word انجام نشد."); console.error(err); } }
}
async function downloadAllAbstracts(){
  if(!S.downloads){ toast("دریافت فایل فقط داخل claude.ai فعال است."); return; }
  try{ const files=[]; for(const v of ARTICLES_SEED.filter(x=>absOf(x.id))) files.push({name:absFile(v.id),data:await buildAbstractDocx(v,absOf(v.id))});
    await S.downloads.save({filename:`ppt-abstracts-${today()}.zip`,data:new Blob([await zipStore(files)],{type:"application/zip"})}); }
  catch(err){ if(!err||err.code!=="declined"){ toast("ساخت فایل ZIP انجام نشد."); console.error(err); } }
}
'''
once("const artStatus = a => (S.artSt[a.id]||{}).status || a.status0 || \"todo\";\n", "const artStatus = a => (S.artSt[a.id]||{}).status || a.status0 || \"todo\";\n" + BLOCK)
once("  const st=artStatus(a), id=esc(a.id), b=[];\n", "  const st=artStatus(a), id=esc(a.id), b=[];\n  if(absOf(a.id)&&S.downloads) b.push(`<button class=\"btn sm\" data-act=\"art-abs\" data-id=\"${id}\" title=\"چکیده طبق قالب همین ژورنال یا کنفرانس، آماده‌ی ثبت در سامانه (فایل Word)\">چکیده (Word)</button>`);\n")
once('<button class="btn" data-act="art-new">افزودن ردیف</button></div>`+\n  table(["حوزه","ژورنال / کنفرانس"', '<button class="btn" data-act="art-new">افزودن ردیف</button>${S.downloads?`<button class="btn sig" data-act="art-abs-all">همه‌ی چکیده‌ها (ZIP)</button>`:""}</div>`+\n  table(["حوزه","ژورنال / کنفرانس"')
once('    case "art-new": artForm(); break;\n', '    case "art-new": artForm(); break;\n    case "art-abs": await downloadAbstract(id); break;\n    case "art-abs-all": await downloadAllAbstracts(); break;\n')
once('ردیف‌های «تأیید شود» را پیش از ارسال در سایت رسمی بررسی کنید و ردیف تازه را خودتان اضافه کنید."}', 'ردیف‌های «تأیید شود» را پیش از ارسال در سایت رسمی بررسی کنید و ردیف تازه را خودتان اضافه کنید. دکمه‌ی «چکیده (Word)» در هر ردیف چکیده‌ی آن مقصد را طبق قالب همان ژورنال یا کنفرانس به‌صورت فایل Word می‌دهد (صفحه‌ی اول متن چکیده، صفحه‌ی دوم برگه‌ی داخلی با ددلاین، قواعد و کارهای پیش از ثبت) و «همه‌ی چکیده‌ها (ZIP)» همه را یک‌جا. جاهای [داخل کروشه] هنوز اندازه‌گیری نشده‌اند؛ پیش از ارسال با نتایج واقعی پر شوند، محدودیت واژه در راهنمای نویسندگان دوباره دیده شود و وکیل ثبت اختراع متن را بازبینی کند."}')
out.write_text(s, encoding="utf-8")
print("ok", len(s))
