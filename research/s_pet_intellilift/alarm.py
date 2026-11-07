"""Instance-level conformal alarm thresholds for well-fault detection (3W-like data).

Per instance: the first `base` samples (labelled normal in 3W) give a robust reference (median / MAD) for every sensor; the
alarm statistic is the largest robust |z| over sensors of a rolling median. The threshold is the conformal quantile of the
per-instance maximum over NORMAL samples of calibration instances, so that a new normal instance raises a false alarm with
probability <= alpha (exchangeability across instances, wells kept apart between calibration and test).
"""
import numpy as np


def reference(x, base):
    ref = x[:base]
    med = np.nanmedian(ref, axis=0)
    mad = np.nanmedian(np.abs(ref - med), axis=0)
    scale = 1.4826 * mad
    floor = 0.01 * np.nanmedian(np.abs(x), axis=0) + 1e-9      # sensors that are constant in the reference
    return med, np.maximum(scale, floor)


def rolling_median(a, w):
    if w <= 1:
        return a
    pad = np.pad(a, ((w - 1, 0), (0, 0)), mode="edge")
    idx = np.arange(a.shape[0])[:, None] + np.arange(w)[None, :]
    return np.stack([np.nanmedian(pad[:, j][idx], axis=1) for j in range(a.shape[1])], 1)


def score(x, base=30, win=5):
    """x: (T, d) sensors, NaN allowed. Returns (T,) alarm statistic; the first `base` samples are the reference (score 0)."""
    med, sc = reference(x, base)
    z = np.abs(rolling_median(x, win) - med) / sc
    s = np.nanmax(np.where(np.isnan(z), -np.inf, z), axis=1)
    s = np.where(np.isfinite(s), s, 0.0)
    s[:base] = 0.0
    return s


def conformal_threshold(max_scores, alpha):
    """Finite-sample conformal quantile of per-instance maxima of normal calibration instances."""
    m = np.sort(np.asarray(max_scores, float)); n = len(m)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else m[k - 1]


def first_alarm(s, thr, start):
    i = np.flatnonzero(s[start:] > thr)
    return None if len(i) == 0 else start + int(i[0])
