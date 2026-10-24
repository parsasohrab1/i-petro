"""Log zonation: PELT change-point segmentation vs a smoothed-gradient peak baseline, scored by boundary F1 with a depth tolerance."""
import numpy as np
import pandas as pd
import ruptures as rpt
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

LOGS = ["GR", "RHOB", "NPHI", "DTC"]


def prep(x):
    x = pd.DataFrame(x).interpolate(limit_direction="both").to_numpy(float)
    x = np.nan_to_num(x, nan=0.0)
    sd = x.std(0); sd[sd == 0] = 1
    return (x - x.mean(0)) / sd


def pelt_boundaries(x, pen, min_size=10):
    return [b for b in rpt.Pelt(model="l2", min_size=min_size, jump=2).fit(x).predict(pen=pen)[:-1]]


def gradient_boundaries(x, thr, sigma=3.0, min_dist=10):
    g = np.linalg.norm(np.gradient(gaussian_filter1d(x, sigma, axis=0), axis=0), axis=1)
    p, _ = find_peaks(g, height=thr, distance=min_dist)
    return list(p)


def f1(pred, true, tol):
    pred, true = np.asarray(pred), np.asarray(true)
    if len(pred) == 0 or len(true) == 0:
        return (0.0, 0, len(pred), len(true))
    tp_p = sum(np.min(np.abs(true - p)) <= tol for p in pred)
    tp_t = sum(np.min(np.abs(pred - t)) <= tol for t in true)
    prec, rec = tp_p / len(pred), tp_t / len(true)
    return (0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec), tp_p, len(pred), len(true))


def true_boundaries(labels):
    lab = pd.Series(labels).ffill().bfill().to_numpy()
    return list(np.flatnonzero(lab[1:] != lab[:-1]) + 1)
