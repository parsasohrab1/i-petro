"""Distribution-free intervals for predicted binding affinity: global split conformal versus Mondrian (stratified) calibration.

The affinity predictor is a black box (a random forest on Morgan fingerprints stands in for the platform's predictor); the uncertainty layer does not depend on it.
Real data: EGFR IC50 values from ChEMBL (via the TeachOpenCADD talktorial data, CC BY 4.0); splits are random or by Bemis-Murcko scaffold (chemical-series shift).
"""
import numpy as np
import pandas as pd
from scipy import stats


def conformal_q(scores, alpha):
    n = len(scores)
    k = min(int(np.ceil((n + 1) * (1 - alpha))), n)
    return float(np.sort(scores)[k - 1])


def bins_from(values, k=3):
    return np.quantile(values, np.linspace(0, 1, k + 1)[1:-1])


class Intervals:
    """mode 'global': one quantile; mode 'mondrian': one quantile per stratum of the *predicted* value (terciles of the calibration predictions)."""

    def __init__(self, alpha=0.1, mode="global", k=3, min_n=30):
        self.alpha, self.mode, self.k, self.min_n = alpha, mode, k, min_n

    def fit(self, pred_cal, y_cal):
        s = np.abs(np.asarray(y_cal) - np.asarray(pred_cal))
        self.q_all = conformal_q(s, self.alpha)
        if self.mode == "mondrian":
            self.edges = bins_from(pred_cal, self.k)
            st = np.digitize(pred_cal, self.edges)
            self.q = {b: (conformal_q(s[st == b], self.alpha) if (st == b).sum() >= self.min_n else self.q_all) for b in range(self.k)}
        return self

    def half_width(self, pred):
        if self.mode == "global":
            return np.full(len(pred), self.q_all)
        st = np.digitize(pred, self.edges)
        return np.array([self.q[b] for b in st])

    def strata(self, pred):
        return np.digitize(pred, self.edges) if self.mode == "mondrian" else np.zeros(len(pred), int)


def coverage_report(y, pred, hw, groups):
    """Marginal coverage, worst group coverage (groups with >= 20 test points) and mean interval width."""
    cov = (np.abs(y - pred) <= hw)
    per = {g: float(cov[groups == g].mean()) for g in np.unique(groups) if (groups == g).sum() >= 20}
    return {"coverage": float(cov.mean()), "worst_group": float(min(per.values())) if per else float("nan"), "width": float(2 * hw.mean())}


def mean_ci(x, level=0.95):
    x = np.asarray(x, float); n = len(x)
    if n < 2:
        return float(x.mean()), float("nan")
    return float(x.mean()), float(stats.t.ppf((1 + level) / 2, n - 1) * x.std(ddof=1) / np.sqrt(n))
