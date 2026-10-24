import numpy as np
from research.s_iqicsa_qgrid import qaoa

TRI = [(0, 1, 1.0), (1, 2, 1.0), (0, 2, 1.0)]


def test_maxcut_diag_triangle():
    d = qaoa.maxcut_diag(3, TRI); assert d.max() == 2 and d[0] == 0


def test_zero_angles_give_mean_cost():
    d = qaoa.maxcut_diag(3, TRI); assert abs(qaoa.expectation(d, 3, np.zeros(2)) - d.mean()) < 1e-12


def test_norm_preserved():
    d = qaoa.maxcut_diag(4, [(0, 1, 2.0), (1, 2, 1.0), (2, 3, 0.5)])
    psi = qaoa.state(d, 4, [0.3, 0.7], [0.2, 0.9]); assert abs(np.linalg.norm(psi) - 1) < 1e-12


def test_p1_ring_known_value():
    # 4-cycle, p=1 QAOA maxcut: optimum expected cut is 3.0 (ratio 0.75) -- known result for rings
    e = [(i, (i + 1) % 4, 1.0) for i in range(4)]; d = qaoa.maxcut_diag(4, e)
    v, _, _ = qaoa.optimise(d, 4, 1, restarts=6); assert 2.9 < v < 3.01


def test_baselines_bounded():
    d = qaoa.maxcut_diag(3, TRI); assert qaoa.greedy_local(3, TRI) <= d.max() + 1e-9 and qaoa.spectral(3, TRI) <= d.max() + 1e-9


def test_spectral_splits_bipartite_graph():
    e = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0)]
    assert abs(qaoa.spectral(4, e) - 4.0) < 1e-9
