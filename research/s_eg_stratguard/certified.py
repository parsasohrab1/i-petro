"""Certified facies sets (split conformal, LAC score), grammar learned from training wells, Viterbi decoding and referral rules.

Written for real well-log data (SEG 2016 facies contest; FORCE 2020 lithology). Synthetic data appear only in the unit tests.
"""
import numpy as np
import pandas as pd

NEG, SET_PENALTY = -1e9, -30.0


def conformal_q(s, alpha):
    n = len(s); k = min(int(np.ceil((n + 1) * (1 - alpha))), n)
    return float(np.sort(s)[k - 1])


def prediction_sets(proba, qhat):
    m = (1 - proba) <= qhat
    m[np.arange(len(proba)), proba.argmax(1)] = True      # never empty
    return m


def learn_grammar(label_seqs, n_classes, min_count=3):
    """A contact a->b is allowed if it occurs at least min_count times in the training wells (stays are always allowed)."""
    C = np.zeros((n_classes, n_classes))
    for y in label_seqs:
        a, b = y[:-1], y[1:]
        np.add.at(C, (a[a != b], b[a != b]), 1)
    G = C >= min_count
    np.fill_diagonal(G, True)
    return G


def violations(path, G):
    p = np.asarray(path)
    return int(sum(not G[a, b] for a, b in zip(p[:-1], p[1:])))


def viterbi(proba, sets, G, stay=0.97):
    n, K = proba.shape
    T = np.full((K, K), NEG)
    for a in range(K):
        allowed = [b for b in range(K) if b != a and G[a, b]]
        T[a, a] = np.log(stay if allowed else 1.0)
        for b in allowed:
            T[a, b] = np.log((1 - stay) / len(allowed))
    E = np.log(np.clip(proba, 1e-9, 1)) + np.where(sets, 0.0, SET_PENALTY)
    delta = np.zeros((n, K)); back = np.zeros((n, K), int); delta[0] = E[0]
    for i in range(1, n):
        c = delta[i - 1][:, None] + T; back[i] = c.argmax(0); delta[i] = c.max(0) + E[i]
    path = np.zeros(n, int); path[-1] = delta[-1].argmax()
    for i in range(n - 1, 0, -1):
        path[i - 1] = back[i, path[i]]
    return path


def boundary_mask(path, reservoir, window):
    res = np.isin(path, list(reservoir)); edge = np.where(res[1:] != res[:-1])[0]
    m = np.zeros(len(path), bool)
    for e in edge:
        m[max(0, e - window): e + window + 2] = True
    return m


def referral(sets, path, reservoir, window, max_size=1, boundary_max_size=1, cost_aware=False, loose_size=2):
    """plain: refer when the set has more than max_size members. cost-aware: stricter (boundary_max_size) near reservoir / non-reservoir contacts, looser (loose_size) elsewhere."""
    size = sets.sum(1)
    if not cost_aware:
        return size > max_size
    return np.where(boundary_mask(path, reservoir, window), size > boundary_max_size, size > loose_size)


def evaluate_well(clf_factory, X, y, wells, test_well, classes, G_min=3, alpha=0.1, n_cal_wells=2, seed=0, reservoir=(), window=20, step=1):
    """Train on all wells except the test well and the calibration wells; calibrate on n_cal_wells random other wells; test on the held-out well."""
    rng = np.random.default_rng(seed)
    others = np.array([w for w in np.unique(wells) if w != test_well])
    cal = rng.choice(others, n_cal_wells, replace=False); train = np.setdiff1d(others, cal)
    mtr, mca, mte = np.isin(wells, train), np.isin(wells, cal), wells == test_well
    clf = clf_factory().fit(X[mtr], y[mtr])
    P = np.zeros((int(mte.sum()), len(classes))); Pc = np.zeros((int(mca.sum()), len(classes)))
    P[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mte]); Pc[:, np.searchsorted(classes, clf.classes_)] = clf.predict_proba(X[mca])
    yc, yt = np.searchsorted(classes, y[mca]), np.searchsorted(classes, y[mte])
    q = conformal_q(1 - Pc[np.arange(len(yc)), yc], alpha)
    S = prediction_sets(P, q)
    G = learn_grammar([np.searchsorted(classes, y[wells == w]) for w in train], len(classes), G_min)
    path = viterbi(P, S, G)
    base = P.argmax(1)
    res_idx = [int(np.searchsorted(classes, r)) for r in reservoir if r in classes]
    out = {"well": str(test_well), "n": int(mte.sum()), "coverage": float(S[np.arange(len(yt)), yt].mean()), "set_size": float(S.sum(1).mean()),
           "acc_base": float((base == yt).mean()), "acc_decoded": float((path == yt).mean()),
           "violations_base": violations(base, G), "violations_decoded": violations(path, G)}
    for name, r in (("plain", referral(S, path, res_idx, window)), ("cost_aware", referral(S, path, res_idx, window, cost_aware=True, boundary_max_size=1, loose_size=2))):
        keep = ~r
        out[f"referral_{name}"] = float(r.mean()); out[f"acc_kept_{name}"] = float((path[keep] == yt[keep]).mean()) if keep.any() else float("nan")
    return out
