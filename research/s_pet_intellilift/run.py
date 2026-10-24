"""python -m research.s_pet_intellilift.run <3W dataset dir>  -> results.json"""
import json, sys, warnings
import numpy as np
from . import alarm, data

warnings.filterwarnings("ignore")
BASE, WIN, FIXED = 30, 5, (5.0, 10.0, 20.0)


def prep(inst):
    out = []
    for r in inst:
        s = alarm.score(r["x"], BASE, WIN)
        out.append(dict(r, s=s))
    return out


def normal_max(r):
    m = (r["y"] == 0); m[:BASE] = False
    return r["s"][m].max() if m.any() else np.nan


def evaluate(inst, alpha, seed):
    rng = np.random.default_rng(seed)
    wells = np.array(sorted({r["well"] for r in inst})); rng.shuffle(wells)
    cal_w = set(wells[: len(wells) // 2])
    cal = [normal_max(r) for r in inst if r["cls"] == 0 and r["well"] in cal_w]
    cal = [c for c in cal if np.isfinite(c)]
    thr = alarm.conformal_threshold(cal, alpha)
    res = dict(thr=float(thr), n_cal=len(cal))
    test = [r for r in inst if r["well"] not in cal_w]
    norm = [r for r in test if r["cls"] == 0 and np.isfinite(normal_max(r))]
    thrs = {"conformal": thr, **{f"fixed{f:g}": f for f in FIXED}}
    for name, t in thrs.items():
        res[f"far_{name}"] = float(np.mean([normal_max(r) > t for r in norm])) if norm else None
        per = {}
        for r in test:
            if r["cls"] == 0 or r["onset"] is None or r["onset"] <= BASE + 5:
                continue
            on = r["onset"]; s = r["s"]
            pre = alarm.first_alarm(s[:on], t, BASE) if on > BASE else None
            post = alarm.first_alarm(s, t, on)
            d = per.setdefault(r["cls"], dict(n=0, det=0, warn=0, post=0, delay=[]))
            d["n"] += 1; d["warn"] += pre is not None; d["post"] = d.get("post", 0) + (post is not None); d["det"] += (pre is not None) or (post is not None)
            first = pre if pre is not None else post
            if first is not None: d["delay"].append(first - on)
        res[f"fault_{name}"] = {str(k): dict(n=v["n"], detect=v["det"] / v["n"], warn_before_onset=v["warn"] / v["n"], alarm_from_onset=v["post"] / v["n"],
                                              median_delay_min=float(np.median(v["delay"])) if v["delay"] else None) for k, v in per.items()}
    return res


def summarise(rs):
    far = [r["far_conformal"] for r in rs if r["far_conformal"] is not None]
    out = dict(runs=len(rs), far_conformal_mean=float(np.mean(far)), far_conformal_sd=float(np.std(far)),
               far_conformal_frac_runs_above_alpha=float(np.mean(np.array(far) > 0.1)), far_conformal_q05_q95=[float(np.quantile(far, .05)), float(np.quantile(far, .95))])
    for k in rs[0]:
        if k.startswith("far_fixed"):
            out[k] = float(np.mean([r[k] for r in rs if r[k] is not None]))
    for name in ["conformal"] + [f"fixed{f:g}" for f in FIXED]:
        agg = {}
        for r in rs:
            for c, v in r[f"fault_{name}"].items():
                a = agg.setdefault(c, dict(n=[], det=[], warn=[], post=[], delay=[]))
                a["n"].append(v["n"]); a["det"].append(v["detect"]); a["warn"].append(v["warn_before_onset"]); a["post"].append(v["alarm_from_onset"])
                if v["median_delay_min"] is not None: a["delay"].append(v["median_delay_min"])
        out[f"fault_{name}"] = {c: dict(mean_test_instances=float(np.mean(a["n"])), detect=float(np.mean(a["det"])),
                                         warn_before_onset=float(np.mean(a["warn"])), alarm_from_onset=float(np.mean(a["post"])),
                                         median_delay_min=float(np.median(a["delay"])) if a["delay"] else None) for c, a in sorted(agg.items())}
    return out


if __name__ == "__main__":
    inst = prep(data.load_real(sys.argv[1]))
    summary = dict(n_instances=len(inst), n_normal=sum(r["cls"] == 0 for r in inst), n_wells=len({r["well"] for r in inst}),
                   by_class={str(c): sum(r["cls"] == c for r in inst) for c in range(10)})
    for alpha in (0.1,):
        rs = [evaluate(inst, alpha, s) for s in range(20)]
        summary[f"alpha_{alpha}"] = summarise(rs)
    json.dump(summary, open("research/s_pet_intellilift/results.json", "w"), indent=1)
    print(json.dumps(summary, indent=1)[:6000])
