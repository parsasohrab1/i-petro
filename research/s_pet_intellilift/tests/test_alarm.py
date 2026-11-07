import numpy as np
from research.s_pet_intellilift import alarm


def synth(T=300, shift_at=None, seed=0):
    x = np.random.default_rng(seed).normal(0, 1, (T, 3)) + 100
    if shift_at is not None:
        x[shift_at:, 1] += 15
    return x


def test_shift_detected_and_normal_quiet():
    thr = alarm.conformal_threshold([alarm.score(synth(seed=s)).max() for s in range(50)], 0.1)
    assert alarm.score(synth(shift_at=150, seed=99)).max() > thr
    fa = np.mean([alarm.score(synth(seed=1000 + s)).max() > thr for s in range(200)])
    assert fa < 0.2


def test_threshold_finite_sample():
    assert alarm.conformal_threshold([1, 2, 3], 0.1) == np.inf
    assert alarm.conformal_threshold(list(range(1, 20)), 0.1) == 18


def test_first_alarm():
    s = np.array([0, 0, 5, 0, 7.0]); assert alarm.first_alarm(s, 1, 3) == 4 and alarm.first_alarm(s, 10, 0) is None
