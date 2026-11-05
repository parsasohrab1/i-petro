import numpy as np
from research.s_iai_fidps import zonation as z


def stepped(seed=0):
    r = np.random.default_rng(seed); x = np.r_[np.zeros(100), 3 * np.ones(100), -2 * np.ones(100)][:, None] + r.normal(0, .3, (300, 1))
    return z.prep(x), [100, 200]


def test_pelt_finds_steps():
    x, t = stepped(); assert z.f1(z.pelt_boundaries(x, 20), t, 5)[0] > 0.9


def test_gradient_finds_steps():
    x, t = stepped(); assert z.f1(z.gradient_boundaries(x, 0.05), t, 5)[0] > 0.5


def test_f1_edge_cases():
    assert z.f1([], [1], 3)[0] == 0 and z.f1([10], [10], 0)[0] == 1.0


def test_true_boundaries():
    assert z.true_boundaries(["a", "a", "b", "b", "c"]) == [2, 4]
