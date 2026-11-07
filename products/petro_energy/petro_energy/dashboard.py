"""Self-contained management dashboard (one HTML file, inline SVG, right-to-left, no external requests)."""
from html import escape as e

W, H = 520, 150


def svg_lines(series, labels=None, colors=("#d12a1f", "#2d64c8", "#1e8a4a"), ymin=None, ymax=None, marks=()):
    pts = [v for s in series for v in s if v is not None]
    lo = min(pts) if ymin is None else ymin
    hi = max(pts) if ymax is None else ymax
    span = (hi - lo) or 1.0
    n = max(len(s) for s in series)
    def xy(i, v): return 36 + (W - 44) * i / max(n - 1, 1), 10 + (H - 24) * (1 - (v - lo) / span)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" width="100%" style="direction:ltr">',
           f'<line x1="36" y1="{H-14}" x2="{W-8}" y2="{H-14}" stroke="#bbb"/>',
           f'<text x="2" y="16" font-size="10" fill="#777" text-anchor="start">{hi:.2f}</text><text x="2" y="{H-16}" font-size="10" fill="#777" text-anchor="start">{lo:.2f}</text>']
    for m in marks:
        x, _ = xy(m, lo)
        out.append(f'<line x1="{x:.1f}" y1="8" x2="{x:.1f}" y2="{H-14}" stroke="#d1600f" stroke-dasharray="3 3"/>')
    for k, s in enumerate(series):
        d = " ".join(f"{'M' if i == 0 else 'L'}{xy(i, v)[0]:.1f},{xy(i, v)[1]:.1f}" for i, v in enumerate(s) if v is not None)
        out.append(f'<path d="{d}" fill="none" stroke="{colors[k % len(colors)]}" stroke-width="1.6"/>')
    out.append("</svg>")
    return "".join(out)


def bars(names, a, b):
    mx = max(a + b) or 1
    rows = []
    for n, x, y in zip(names, a, b):
        rows.append(f'<div class="br"><span>{e(n)}</span><div><i style="width:{100*x/mx:.0f}%;background:#2d64c8"></i><b>{x:.0f}</b></div>'
                    f'<div><i style="width:{100*y/mx:.0f}%;background:#1e8a4a"></i><b>{y:.0f}</b></div></div>')
    return "".join(rows)


def build(plant, rows, res, truth):
    nd = len(rows) // 24
    fur_rows = []
    for f in plant.furnaces:
        pf = res["furnaces"][f.id]
        o2_now = sum(pf["o2"]) / len(pf["o2"])
        o2_opt = sum(pf["o2_opt"]) / len(pf["o2_opt"])
        fur_rows.append(f'<tr><td>{e(f.id)}</td><td>{o2_now:.1f}</td><td>{o2_opt:.1f}</td><td>{sum(pf["eff"])/len(pf["eff"]):.1f}</td>'
                        f'<td>{pf["fouling_c_per_day"]:+.2f}</td><td>{pf["save"]/len(pf["o2"]):.2f}</td></tr>')
    alerts = "".join(f'<li>ساعت {h} (روز {h//24+1}): افزایش ناگهانی اکسیژن کوره‌ی {e(fid)} (z={z:.0f}) – احتمال نشت هوا یا خطای دمپر</li>' for h, fid, z in res["flags"]) or "<li>هشداری ثبت نشد.</li>"
    foul = [(f.id, res["furnaces"][f.id]["fouling_c_per_day"]) for f in plant.furnaces if res["furnaces"][f.id]["fouling_c_per_day"] > 0.5]
    foul_txt = "".join(f"<li>کوره‌ی {e(i)}: دمای دودکش {s:+.2f} درجه در روز بالا می‌رود؛ بازدید یا تمیزکاری بخش همرفتی پیشنهاد می‌شود.</li>" for i, s in foul)
    eff_daily = [sum(res["eff_series"][d*24:(d+1)*24]) / 24 for d in range(nd)] if plant.furnaces else []
    charts = f'<h3>مصرف ویژه‌ی انرژی (مگاوات‌ساعت به‌ازای هر تن محصول، روزانه)</h3>{svg_lines([res["sec_daily"]])}'
    if plant.furnaces:
        f0 = plant.furnaces[0]
        lo, hi = max(0, truth["leak_start"] - 48), min(len(rows), truth["leak_start"] + 72)
        pf = res["furnaces"][f0.id]
        charts += (f'<h3>راندمان میانگین کوره‌ها (٪، روزانه)</h3>{svg_lines([eff_daily])}'
                   f'<h3>اکسیژن دودکش کوره‌ی {e(f0.id)}: واقعی (قرمز) و توصیه‌ی بهینه‌ساز (آبی)</h3>'
                   f'{svg_lines([pf["o2"][lo:hi], pf["o2_opt"][lo:hi]], marks=[truth["leak_start"]-lo])}')
    sav = res["saving_pct"]
    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PetroEnergy – {e(plant.name_fa)}</title><style>
body{{font:14px/1.8 Vazirmatn,Tahoma,sans-serif;margin:0;background:#f5f4f3;color:#171515}}main{{max-width:980px;margin:0 auto;padding:16px}}
.tag{{background:#fbe9e7;border:1px solid #d12a1f;border-radius:8px;padding:8px 12px;margin:10px 0}}
.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}}.k div{{background:#fff;border:1px solid #dcd8d6;border-radius:8px;padding:8px 12px}}
.k b{{display:block;font:500 22px ui-monospace,monospace;direction:ltr;text-align:right}}.k span{{color:#615b59;font-size:12px}}
section{{background:#fff;border:1px solid #dcd8d6;border-radius:8px;padding:6px 14px;margin:12px 0}}table{{border-collapse:collapse;width:100%}}th,td{{border-bottom:1px solid #eee;padding:6px;text-align:right}}
.br{{display:grid;grid-template-columns:70px 1fr 1fr;gap:6px;align-items:center;margin:4px 0}}.br div{{background:#f0eeed;height:18px;position:relative}}.br i{{display:block;height:18px}}.br b{{position:absolute;inset-inline-start:4px;top:0;font-size:11px}}
</style></head><body><main>
<h1>داشبورد مدیریتی کنترل سوخت و انرژی – {e(plant.name_fa)}</h1><p>{e(plant.name_en)} · PetroEnergy v0.1 · پترو پالاتوس</p>
<div class="tag"><b>TRL 4 – اعتبارسنجی آزمایشگاهی با داده‌ی ساختگی.</b> همه‌ی اعداد این صفحه از شبیه‌سازی ۳۰ روزه با پارامترهای نمونه به‌دست آمده‌اند و اندازه‌گیری واقعی {e(plant.name_fa)} نیستند. ارتقا به TRL 5 فقط با داده‌ی واقعی واحد و اندازه‌گیری در برابر خط مبنا ممکن است.</div>
<div class="k"><div><b>{res['sec_mwh_per_t']:.2f}</b><span>مصرف ویژه (MWh/t)</span></div><div><b>{res['sec_opt_mwh_per_t']:.2f}</b><span>با بهینه‌سازی (MWh/t)</span></div>
<div><b>{sav:.2f}٪</b><span>کاهش سوخت در مدل</span></div><div><b>{'—' if res['avg_furnace_eff'] is None else f"{res['avg_furnace_eff']:.1f}٪"}</b><span>راندمان میانگین کوره‌ها</span></div><div><b>{len(res['flags'])}</b><span>هشدار خطا</span></div></div>
<section>{charts}</section>
<section><h3>تقسیم بار دیگ‌های بخار در آخرین ساعت (t/h): رایج (آبی) و کم‌سوخت‌ترین (سبز)</h3>{bars([b.id for b in plant.boilers], res['last_loads_now'], res['last_loads_opt'])}</section>
{'<section><h3>کوره‌ها</h3><table><tr><th>کوره</th><th>O₂ واقعی ٪</th><th>O₂ توصیه ٪</th><th>راندمان ٪</th><th>روند دمای دودکش °C/روز</th><th>صرفه‌جویی MW</th></tr>' + ''.join(fur_rows) + '</table></section>' if fur_rows else ''}
<section><h3>هشدارها و توصیه‌ها</h3><ul>{alerts}{foul_txt}</ul></section>
<p style="color:#615b59;font-size:12px">روش: راندمان کوره با روش افت دودکش (Siegert، گاز طبیعی) و جریمه‌ی احتراق ناقص؛ بهینه‌ساز O₂ هرگز زیر حد ایمن CO نمی‌رود؛ تقسیم بار دیگ‌ها با کمینه‌سازی افزایشی سوخت؛ آشکارساز نشت هوا بر پایه‌ی انحراف مقاومِ O₂.</p>
</main></body></html>"""
