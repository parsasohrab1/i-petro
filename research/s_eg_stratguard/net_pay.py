"""Decision-level analysis: certified bounds on the reservoir fraction of a well.

Question a petrophysicist asks: how much of this well is reservoir-quality rock, and can the sets bound it?
For every held-out well we compute (depth samples are equally spaced after subsampling, so fractions stand for thickness fractions):
  true fraction       = share of depths whose true class is a reservoir class
  base estimate       = share of depths whose argmax class is a reservoir class
  certain lower bound = share of depths whose whole conformal set is reservoir classes
  possible upper bound= share of depths whose set contains at least one reservoir class
The bound is "covered" when true fraction lies in [lower, upper]. Calibration: pooled wells (as in the main study) or well-local with m labelled depths.
Reservoir class sets are the assumption already stated in data.py. Real data only.
"""
import json
import sys

import numpy as np

from . import certified as c
from . import data
from .run import make_clf


def one_well(X, y, wells, test_well, classes, reservoir, alpha=0.1, n_cal_wells=2, seed=0, m=100):
    rng = np.random.default_rng(seed)
    others = np.array([w for w in np.unique(wells) if w != test_well])
    cal = rng.choice(others, n_cal_wells, replace=False); train = np.setdiff1d(others, cal)
    mtr, mca, mte = np.isin(wells, train), np.isin(wells, cal), wells == test_well
    clf = make_clf().fit(X[mtr], y[mtr])
    P = np.zeros((int(mte.sum()), len(classes))); Pc = np.zeros((int(mca.sum()), len(classes)))
    P[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mte]); Pc[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mca])
    yc, yt = np.searchsorted(classes, y[mca]), np.searchsorted(classes, y[mte])
    s_pool = 1 - Pc[np.arange(len(yc)), yc]; s_test = 1 - P[np.arange(len(yt)), yt]
    res = np.zeros(len(classes), bool)
    for r in reservoir:
        if r in classes:
            res[int(np.searchsorted(classes, r))] = True
    order = rng.permutation(len(yt)); lab, rest = order[:m], order[m:]
    out = {"well": str(test_well)}
    true_f = float(res[yt[rest]].mean()); base_f = float(res[P[rest].argmax(1)].mean())
    out["true"] = true_f; out["base"] = base_f; out["base_abs_err"] = abs(base_f - true_f)
    for name, q in (("pooled", c.conformal_q(s_pool, alpha)), ("local", c.conformal_q(s_test[lab], alpha))):
        S = c.prediction_sets(P[rest], q)
        lo = float((S & res).sum(1).astype(int).__eq__(S.sum(1)).mean()); hi = float((S & res).any(1).mean())
        out[f"{name}_lo"] = lo; out[f"{name}_hi"] = hi; out[f"{name}_covered"] = bool(lo - 1e-12 <= true_f <= hi + 1e-12); out[f"{name}_width"] = hi - lo
    return out


def run(X, y, wells, reservoir, seeds=(0, 1, 2), m=100):
    classes = np.unique(y); rows = []
    for w in np.unique(wells):
        if (wells == w).sum() < 50 + m:
            continue
        for s in seeds:
            rows.append(one_well(X, y, wells, w, classes, reservoir, seed=s, m=m))
    return rows


def summarise(rows):
    import pandas as pd
    d = pd.DataFrame(rows); w = d.groupby("well").agg({"true": "mean", "base": "mean", "base_abs_err": "mean", "pooled_covered": "mean", "local_covered": "mean",
                                                          "pooled_width": "mean", "local_width": "mean", "pooled_lo": "mean", "pooled_hi": "mean", "local_lo": "mean", "local_hi": "mean"})
    return {"n_wells": int(len(w)), "mean_true_reservoir_fraction": round(float(w.true.mean()), 3), "base_mean_abs_error": round(float(w.base_abs_err.mean()), 3),
            "base_wells_err_above_0.10": int((w.base_abs_err > 0.10).sum()),
            "pooled_bound_covers_true_share": round(float(w.pooled_covered.mean()), 3), "pooled_mean_width": round(float(w.pooled_width.mean()), 3),
            "local_bound_covers_true_share": round(float(w.local_covered.mean()), 3), "local_mean_width": round(float(w.local_width.mean()), 3)}


if __name__ == "__main__":
    seg_csv, force_csv = sys.argv[1], sys.argv[2]
    out = {}
    X, y, w = data.load_seg(seg_csv); rows = run(X, y, w, data.SEG_RESERVOIR); out["SEG2016"] = summarise(rows); print("SEG2016", out["SEG2016"])
    X, y, w = data.load_force(force_csv); rows = run(X, y, w, data.FORCE_RESERVOIR, seeds=(0,)); out["FORCE2020"] = summarise(rows); print("FORCE2020", out["FORCE2020"])
    json.dump(out, open("research/s_eg_stratguard/results_net_pay.json", "w"), indent=1)


def naive_interval(rows_cal_err, base_f, q=0.9):
    """Naive baseline: point estimate +/- the empirical q-quantile of |error| measured on other wells."""
    e = float(np.quantile(rows_cal_err, q))
    return max(0.0, base_f - e), min(1.0, base_f + e)
