import numpy as np

from research.s_iqim_hqca import affinity_conformal as ac, egfr


def test_conformal_quantile_rank():
    s = np.arange(1, 10, dtype=float)                      # n = 9, alpha 0.2 -> k = ceil(10*0.8) = 8
    assert ac.conformal_q(s, 0.2) == 8.0 and ac.conformal_q(s, 0.01) == 9.0


def test_global_coverage_on_exchangeable_data():
    rng = np.random.default_rng(0)
    pred = rng.normal(size=6000); y = pred + rng.normal(size=6000)
    iv = ac.Intervals(0.1).fit(pred[:3000], y[:3000])
    assert abs(ac.coverage_report(y[3000:], pred[3000:], iv.half_width(pred[3000:]), np.zeros(3000, int))["coverage"] - 0.9) < 0.03


def test_mondrian_restores_coverage_in_every_stratum_when_noise_depends_on_prediction():
    rng = np.random.default_rng(1)
    pred = rng.uniform(0, 3, 12000); y = pred + rng.normal(size=12000) * (0.2 + pred)         # heteroscedastic
    g = ac.Intervals(0.1, "global").fit(pred[:6000], y[:6000]); m = ac.Intervals(0.1, "mondrian").fit(pred[:6000], y[:6000])
    st = m.strata(pred[6000:])
    rg = ac.coverage_report(y[6000:], pred[6000:], g.half_width(pred[6000:]), st); rm = ac.coverage_report(y[6000:], pred[6000:], m.half_width(pred[6000:]), st)
    assert rg["worst_group"] < 0.85 and rm["worst_group"] > 0.87


def test_scaffold_split_keeps_groups_together_and_covers_everything():
    scaf = np.array([f"s{i % 40}" for i in range(2000)])
    tr, ca, te = egfr.scaffold_split(scaf, np.random.default_rng(0))
    assert not (set(scaf[tr]) & set(scaf[te])) and not (set(scaf[tr]) & set(scaf[ca])) and len(tr) + len(ca) + len(te) == len(scaf)


def test_featuriser_skips_invalid_smiles():
    X, scaf, keep = egfr.featurise(["CCO", "not_a_smiles", "c1ccccc1O"])
    assert X.shape == (2, 2048) and list(keep) == [0, 2]


def test_mean_ci():
    m, h = ac.mean_ci([1, 2, 3, 4, 5]); assert m == 3 and 1.9 < h < 2.0
