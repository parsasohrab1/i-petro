"""Remaining-useful-life estimates and a conservative lower bound with a calibrated one-sided error quantile."""
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression


def health_index(d, base_frac=0.1, window=15):
    """Smoothed log RMS relative to the early-life level (label-free: uses no failure information)."""
    n = max(int(len(d) * base_frac), 5)
    base = d.rms.iloc[:n].median()
    hi = np.log(d.rms / base)
    return hi.rolling(window, min_periods=1).median().to_numpy()


class ConstantLife:
    """Baseline: every bearing lives the mean training life; RUL = mean life - age."""

    def fit(self, series):
        self.life = float(np.mean([s.t.iloc[-1] for s in series])); return self

    def predict(self, d):
        return np.maximum(self.life - d.t.to_numpy(), 0)


class HIRegressor:
    """Monotone (non-increasing) map from the health index to RUL in hours, fitted on the pooled training bearings."""

    def fit(self, series):
        x = np.concatenate([health_index(s) for s in series]); y = np.concatenate([s.rul.to_numpy() for s in series])
        self.m = IsotonicRegression(increasing=False, out_of_bounds="clip").fit(x, y); return self

    def predict(self, d):
        return self.m.predict(health_index(d))


def overestimation_quantile(model_cls, series, alpha=0.1):
    """(1-alpha) quantile of (prediction - truth) from inner leave-one-bearing-out predictions on the training bearings (never negative)."""
    errs = []
    for i, s in enumerate(series):
        m = model_cls().fit([x for j, x in enumerate(series) if j != i])
        errs.append(m.predict(s) - s.rul.to_numpy())
    return float(max(np.quantile(np.concatenate(errs), 1 - alpha), 0))


def lower_bound(pred, q):
    return np.maximum(np.asarray(pred) - q, 0)
