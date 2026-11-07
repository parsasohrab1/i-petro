import numpy as np
import pandas as pd

from research.s_isie_apexasset import evaluate, ims, rul


def fake_series(life, n=400, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, life, n)
    rms = 0.1 * np.exp(2.5 * (t / life) ** 3) * np.exp(rng.normal(0, 0.03, n))
    return pd.DataFrame({"t": t, "rul": life - t, "rms": rms})


def test_operating_hours_collapses_pauses():
    ts = ["2003-10-22 12:00", "2003-10-22 12:10", "2003-10-23 09:00", "2003-10-23 09:10"]
    t = ims.operating_hours(ts)
    assert np.allclose(t, [0, 10 / 60, 20 / 60, 30 / 60])


def test_isotonic_map_is_monotone_and_ordered():
    train = [fake_series(300, seed=1), fake_series(500, seed=2)]
    p = rul.HIRegressor().fit(train).predict(fake_series(400, seed=3))
    assert (np.diff(p) <= 1e-9).all() or p[0] >= p[-1]


def test_lower_bound_never_exceeds_point_and_is_nonnegative():
    pred = np.array([10.0, 50.0, 200.0]); lb = rul.lower_bound(pred, 30)
    assert (lb <= pred).all() and (lb >= 0).all() and lb[0] == 0


def test_overestimation_quantile_is_nonnegative_and_grows_with_confidence():
    s = [fake_series(300 + 50 * i, seed=i) for i in range(4)]
    assert rul.overestimation_quantile(rul.HIRegressor, s, 0.1) >= 0
    assert rul.overestimation_quantile(rul.HIRegressor, s, 0.05) >= rul.overestimation_quantile(rul.HIRegressor, s, 0.2)


def test_lower_bound_is_safer_than_point_on_fixture():
    series = {("T1", 3): fake_series(300, seed=1), ("T1", 4): fake_series(350, seed=2), ("T2", 1): fake_series(400, seed=3), ("T3", 3): fake_series(500, seed=4)}
    r = evaluate.run(None, series=series).set_index(["held_out", "method"])
    assert (r.xs("lower_bound", level="method").unsafe_all <= r.xs("point", level="method").unsafe_all + 1e-9).all()
