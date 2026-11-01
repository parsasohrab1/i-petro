"""Few-shot well-local recalibration of conformal facies sets.

Idea: the pooled calibration wells give a marginal guarantee but not a per-well one. If a geologist labels a handful (m) of depths in the NEW well,
the conformal threshold can be recomputed from those depths (local) or from the pooled scores plus those depths (mixed). Written for real data;
synthetic data appear only in the unit tests.
"""
import numpy as np
from . import certified as c


def evaluate_well_local(clf_factory, X, y, wells, test_well, classes, ms=(0, 20, 50, 100), alpha=0.1, n_cal_wells=2, seed=0):
    rng = np.random.default_rng(seed)
    others = np.array([w for w in np.unique(wells) if w != test_well])
    cal = rng.choice(others, n_cal_wells, replace=False); train = np.setdiff1d(others, cal)
    mtr, mca, mte = np.isin(wells, train), np.isin(wells, cal), wells == test_well
    clf = clf_factory().fit(X[mtr], y[mtr])
    P = np.zeros((int(mte.sum()), len(classes))); Pc = np.zeros((int(mca.sum()), len(classes)))
    P[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mte]); Pc[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mca])
    yc, yt = np.searchsorted(classes, y[mca]), np.searchsorted(classes, y[mte])
    s_pool = 1 - Pc[np.arange(len(yc)), yc]; s_test = 1 - P[np.arange(len(yt)), yt]
    out = {"well": str(test_well)}
    order = rng.permutation(len(yt))
    for m in ms:
        lab, rest = order[:m], order[m:]
        for name in ("pooled", "local", "mixed"):
            if name == "pooled" or m == 0:
                q = c.conformal_q(s_pool, alpha)
            elif name == "local":
                q = c.conformal_q(s_test[lab], alpha)
            else:
                q = c.conformal_q(np.r_[s_pool, np.repeat(s_test[lab], 5)], alpha)    # local depths weighted 5x
            S = c.prediction_sets(P[rest], q)
            out[f"cov_{name}_m{m}"] = float(S[np.arange(len(rest)), yt[rest]].mean()); out[f"size_{name}_m{m}"] = float(S.sum(1).mean())
    return out
