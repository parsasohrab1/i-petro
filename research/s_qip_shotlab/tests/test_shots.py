import numpy as np
import openfermion as of
from research.s_qip_shotlab import shots


def toy():
    qop = of.QubitOperator("Z0", 1.0) + of.QubitOperator("X0 X1", 0.5) + of.QubitOperator("Z0 Z1", -0.7)
    psi = np.array([1, 0, 0, 1], complex) / np.sqrt(2)          # Bell state: <Z0>=0, <XX>=1, <ZZ>=1
    return qop, psi


def test_term_expectations():
    qop, psi = toy(); ce = shots.term_expectations(qop, psi, 2)
    d = {round(c, 3): round(e, 3) for c, e in ce}; assert d[0.5] == 1.0 and d[-0.7] == 1.0 and d[1.0] == 0.0


def test_oracle_not_worse_than_uniform():
    ce = np.array([[1.0, 0.0], [0.5, 1.0], [0.1, 0.3]]); a = shots.allocations(ce)
    v = {k: shots.alloc_variance(ce, w, 1000) for k, w in a.items()}
    assert v["oracle_abs_c_sigma"] <= min(v["uniform"], v["weighted_abs_c"]) + 1e-12


def test_shadow_mc_unbiased_scale():
    qop, psi = toy(); terms = [(float(c), t) for t, c in qop.terms.items()]
    v, m = shots.shadow_variance_mc(psi, 2, terms, total=200, reps=60, seed=1)
    exact = 0.5 - 0.7                                              # <Z0>=0, <XX>=1, <ZZ>=1
    assert 0 < v < 10 and abs(m - exact) < 4 * np.sqrt(v / 60)
