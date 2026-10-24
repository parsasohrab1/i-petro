import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from . import certified, data


def make_clf():
    return HistGradientBoostingClassifier(max_iter=120, learning_rate=0.1, max_leaf_nodes=15, random_state=0)


def run(X, y, wells, reservoir, window, seeds=(0, 1, 2), test_wells=None, **kw):
    classes = np.unique(y); rows = []
    for w in (test_wells if test_wells is not None else np.unique(wells)):
        if (wells == w).sum() < 50:
            continue
        for s in seeds:
            rows.append(certified.evaluate_well(make_clf, X, y, wells, w, classes, seed=s, reservoir=reservoir, window=window, **kw) | {"seed": s})
    return pd.DataFrame(rows)


def summarise(df):
    w = df.groupby("well").mean(numeric_only=True)
    m = w.mean(); lo = w.coverage.min()
    return {"n_wells": int(len(w)), "coverage_mean": round(float(m.coverage), 3), "coverage_worst_well": round(float(lo), 3), "coverage_wells_below_0.85": int((w.coverage < 0.85).sum()),
            "set_size": round(float(m.set_size), 2), "acc_base": round(float(m.acc_base), 3), "acc_decoded": round(float(m.acc_decoded), 3),
            "violations_base": round(float(w.violations_base.sum()), 0), "violations_decoded": round(float(w.violations_decoded.sum()), 0),
            "referral_plain": round(float(m.referral_plain), 3), "acc_kept_plain": round(float(m.acc_kept_plain), 3),
            "referral_cost_aware": round(float(m.referral_cost_aware), 3), "acc_kept_cost_aware": round(float(m.acc_kept_cost_aware), 3)}


if __name__ == "__main__":
    seg_csv, force_csv = sys.argv[1], sys.argv[2]
    out = {}
    X, y, w = data.load_seg(seg_csv)
    out["SEG2016"] = summarise(run(X, y, w, data.SEG_RESERVOIR, 20)); print("SEG2016", out["SEG2016"])
    X, y, w = data.load_force(force_csv)
    out["FORCE2020"] = summarise(run(X, y, w, data.FORCE_RESERVOIR, 20, seeds=(0,))); print("FORCE2020", out["FORCE2020"])
    json.dump(out, open("research/s_eg_stratguard/results.json", "w"), indent=1)
