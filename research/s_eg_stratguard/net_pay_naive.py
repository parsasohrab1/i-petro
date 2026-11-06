"""Naive-interval baseline for the reservoir-fraction bound (leave-one-well-out on the per-well errors of the base classifier).
For each well the half-width is the 0.9 quantile of |base - true| over the OTHER wells; covers when true lies in base +/- half-width."""
import json
import sys

import numpy as np
import pandas as pd

from . import data
from .net_pay import naive_interval, run


def summarise(rows):
    d = pd.DataFrame(rows).groupby("well").mean(numeric_only=True)
    err = d.base_abs_err.to_numpy(); cov = []; wid = []
    for i in range(len(d)):
        lo, hi = naive_interval(np.delete(err, i), float(d.base.iloc[i]))
        cov.append(lo <= d.true.iloc[i] <= hi); wid.append(hi - lo)
    return {"n_wells": int(len(d)), "naive_covers_true_share": round(float(np.mean(cov)), 3), "naive_mean_width": round(float(np.mean(wid)), 3),
            "conformal_pooled_covers": round(float(d.pooled_covered.mean()), 3), "conformal_pooled_width": round(float(d.pooled_width.mean()), 3)}


if __name__ == "__main__":
    out = {}
    X, y, w = data.load_seg(sys.argv[1]); out["SEG2016"] = summarise(run(X, y, w, data.SEG_RESERVOIR)); print("SEG2016", out["SEG2016"])
    X, y, w = data.load_force(sys.argv[2]); out["FORCE2020"] = summarise(run(X, y, w, data.FORCE_RESERVOIR, seeds=(0,))); print("FORCE2020", out["FORCE2020"])
    json.dump(out, open("research/s_eg_stratguard/results_net_pay_naive.json", "w"), indent=1)
