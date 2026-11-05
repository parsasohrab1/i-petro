import numpy as np
from research.s_icqe_stretchwatch import stretch


def test_entropy_zero_for_pure_occupations():
    assert stretch.entropy_from_occ([2, 2, 0, 0]) < 1e-9


def test_entropy_max_for_half_filled():
    assert abs(stretch.entropy_from_occ([1.0]) - np.log(2)) < 1e-9


def test_h2_equilibrium_matches_literature():
    p = stretch.point("H2", 0.74)
    assert abs(p["e_fci"] - (-1.1373)) < 2e-3 and p["overlap2"] > 0.97


def test_overlap_drops_on_stretching():
    assert stretch.point("H2", 4.0)["overlap2"] < 0.6
