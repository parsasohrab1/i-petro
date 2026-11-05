"""python -m research.s_iai_fidps.run <FORCE 2020 train.csv> -> results.json
Ground truth = stratigraphic GROUP boundaries of FORCE 2020 wells (a surrogate for zonation; NOT formation-damage data)."""
import json, sys, warnings
import numpy as np
import pandas as pd
from . import zonation as z

warnings.filterwarnings("ignore")
STEP, TOL_M = 10, 15.0            # every 10th sample (~1.5 m), tolerance 15 m


def load(path):
    d = pd.read_csv(path, sep=";", usecols=["WELL", "DEPTH_MD", "GROUP"] + z.LOGS)
    out = []
    for w, g in d.sort_values(["WELL", "DEPTH_MD"]).groupby("WELL"):
        g = g.iloc[::STEP]
        if g.GROUP.notna().sum() < 300 or g[z.LOGS].notna().mean().min() < 0.5: continue
        tb = z.true_boundaries(g.GROUP.to_numpy(object)); dep = g.DEPTH_MD.to_numpy()
        out.append(dict(well=w, x=z.prep(g[z.LOGS].to_numpy(float)), dep=dep, true=tb, step_m=float(np.median(np.diff(dep)))))
    return out


def score(wells, method, param):
    tp = npred = ntrue = 0
    for w in wells:
        pred = z.pelt_boundaries(w["x"], param) if method == "pelt" else z.gradient_boundaries(w["x"], param)
        _, a, b, c = z.f1(pred, w["true"], TOL_M / w["step_m"]); tp += a; npred += b; ntrue += c
    # micro-averaged F1 over wells (precision uses predicted boundaries matched, recall true boundaries matched approximated by tp/ntrue)
    p, r = tp / max(npred, 1), tp / max(ntrue, 1)
    return (0 if p + r == 0 else 2 * p * r / (p + r)), npred / len(wells)


def random_f1(wells, seed=0, reps=20):
    rng = np.random.default_rng(seed); res = []
    for _ in range(reps):
        tp = npred = ntrue = 0
        for w in wells:
            n = len(w["x"]); k = max(1, len(w["true"]))
            _, a, b, c = z.f1(rng.integers(0, n, k), w["true"], TOL_M / w["step_m"]); tp += a; npred += b; ntrue += c
        p, r = tp / npred, tp / ntrue; res.append(0 if p + r == 0 else 2 * p * r / (p + r))
    return float(np.mean(res))


if __name__ == "__main__":
    wells = load(sys.argv[1]); rng = np.random.default_rng(0); idx = rng.permutation(len(wells))
    res = dict(n_wells=len(wells), mean_true_boundaries=float(np.mean([len(w["true"]) for w in wells])), tol_m=TOL_M, splits=[])
    for s in range(5):
        idx = np.random.default_rng(s).permutation(len(wells)); tr = [wells[i] for i in idx[: len(wells) // 2]]; te = [wells[i] for i in idx[len(wells) // 2:]]
        best = {}
        for method, grid in (("pelt", [5, 10, 20, 40, 80, 160]), ("gradient", [0.05, 0.1, 0.2, 0.4, 0.8])):
            sc = [(score(tr, method, g)[0], g) for g in grid]; f_tr, g = max(sc)
            f_te, npred = score(te, method, g); best[method] = dict(param=g, f1_train=f_tr, f1_test=f_te, boundaries_per_well=npred)
        best["random_same_count_f1_test"] = random_f1(te, s)
        res["splits"].append(best)
        print(s, best)
    for m in ("pelt", "gradient"):
        v = [sp[m]["f1_test"] for sp in res["splits"]]; res[f"{m}_f1_test_mean"] = float(np.mean(v)); res[f"{m}_f1_test_sd"] = float(np.std(v))
    res["random_f1_test_mean"] = float(np.mean([sp["random_same_count_f1_test"] for sp in res["splits"]]))
    json.dump(res, open("research/s_iai_fidps/results.json", "w"), indent=1)
    print({k: v for k, v in res.items() if k != "splits"})
