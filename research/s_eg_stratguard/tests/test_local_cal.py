"""SYNTHETIC wells (generated here): the new well is harder than the calibration wells, so pooled calibration under-covers."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from research.s_eg_stratguard import local_cal


def make(seed=0):
    rng = np.random.default_rng(seed); X, y, w = [], [], []
    for k in range(6):
        noise = 2.5 if k == 5 else 0.8
        yy = rng.integers(0, 3, 400); xx = rng.normal(size=(400, 2)) * noise + np.c_[yy, -yy]; X.append(xx); y.append(yy); w += [f"w{k}"] * 400
    return np.vstack(X), np.concatenate(y), np.array(w)


def test_local_recalibration_improves_coverage_in_a_harder_well():
    X, y, w = make(); r = [local_cal.evaluate_well_local(lambda: LogisticRegression(max_iter=300), X, y, w, "w5", np.arange(3), ms=(0, 100), seed=s) for s in range(5)]
    pooled = np.mean([x["cov_pooled_m100"] for x in r]); local = np.mean([x["cov_local_m100"] for x in r])
    assert pooled < 0.85 and abs(local - 0.9) < abs(pooled - 0.9)
