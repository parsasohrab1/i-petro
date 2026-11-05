import numpy as np
from sklearn.ensemble import RandomForestClassifier

from research.s_eg_stratguard import certified as c


def test_conformal_sets_cover_and_are_never_empty():
    rng = np.random.default_rng(0)
    P = rng.dirichlet(np.ones(4), 5000); y = np.array([rng.choice(4, p=p) for p in P])
    q = c.conformal_q(1 - P[np.arange(2500), y[:2500]], 0.1)
    S = c.prediction_sets(P[2500:], q)
    assert S.any(1).all() and abs(S[np.arange(2500), y[2500:]].mean() - 0.9) < 0.03


def test_grammar_learned_from_contacts_and_decoder_respects_it():
    seqs = [np.array([0] * 20 + [1] * 20 + [2] * 20)] * 5
    G = c.learn_grammar(seqs, 3, min_count=3)
    assert G[0, 1] and G[1, 2] and not G[0, 2] and G.diagonal().all()
    rng = np.random.default_rng(1); P = rng.dirichlet(np.ones(3), 60); P[:, 0] += 0.5; P /= P.sum(1, keepdims=True)
    path = c.viterbi(P, np.ones((60, 3), bool), G)
    assert c.violations(path, G) == 0


def test_boundary_mask_and_cost_aware_referral():
    path = np.array([0] * 30 + [1] * 30)
    m = c.boundary_mask(path, {0}, 3); assert m[28:33].all() and not m[:20].any()
    S = np.zeros((60, 2), bool); S[:, 0] = True; S[:, 1] = True            # all sets have size 2
    plain = c.referral(S, path, {0}, 3, max_size=2); ca = c.referral(S, path, {0}, 3, cost_aware=True, boundary_max_size=1, loose_size=2)
    assert not plain.any() and ca.sum() == m.sum()


def test_evaluate_well_end_to_end_on_separable_data():
    rng = np.random.default_rng(2)
    wells, X, y = [], [], []
    for w in range(6):
        lab = np.repeat([0, 1, 2, 1, 0], 60)
        X.append(lab[:, None] * 2.0 + rng.normal(0, 0.6, (300, 1))); y.append(lab); wells += [f"w{w}"] * 300
    X, y, wells = np.vstack(X), np.concatenate(y), np.array(wells)
    r = c.evaluate_well(lambda: RandomForestClassifier(50, random_state=0), X, y, wells, "w0", np.array([0, 1, 2]), alpha=0.1, reservoir=(0,))
    assert r["coverage"] >= 0.8 and r["acc_decoded"] > 0.8 and r["violations_decoded"] == 0
