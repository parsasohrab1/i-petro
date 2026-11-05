"""Exact state-vector QAOA for diagonal cost functions, plus classical baselines for graph bipartition (numpy/scipy only)."""
import numpy as np
from scipy.optimize import minimize


def bits(n):
    return ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(np.int8)       # (2^n, n); bit i = qubit i


def maxcut_diag(n, edges):
    b = bits(n); c = np.zeros(2 ** n)
    for i, j, w in edges:
        c += w * (b[:, i] != b[:, j])
    return c


def _rx_all(psi, n, beta):
    c, s = np.cos(beta), -1j * np.sin(beta)
    psi = psi.reshape((2,) * n)
    for ax in range(n):
        a0 = np.take(psi, 0, axis=ax); a1 = np.take(psi, 1, axis=ax)
        psi = np.stack([c * a0 + s * a1, s * a0 + c * a1], axis=ax)
    return psi.reshape(-1)


def state(diag, n, gammas, betas):
    psi = np.full(2 ** n, 2 ** (-n / 2), dtype=complex)
    for g, b in zip(gammas, betas):
        psi = _rx_all(np.exp(-1j * g * diag) * psi, n, b)
    return psi


def expectation(diag, n, params):
    p = len(params) // 2
    psi = state(diag, n, params[:p], params[p:])
    return float(np.real(np.vdot(psi, diag * psi)))


def optimise(diag, n, p, restarts=5, seed=0, maxiter=300, maximise=True):
    """COBYLA from random starts; returns (best expectation, params, number of function evaluations in total)."""
    rng = np.random.default_rng(seed); sgn = -1.0 if maximise else 1.0
    scale = np.pi / max(np.abs(diag).max(), 1e-9)
    best, nev = None, 0
    for _ in range(restarts):
        x0 = np.concatenate([rng.uniform(0, scale, p), rng.uniform(0, np.pi / 2, p)])
        r = minimize(lambda x: sgn * expectation(diag, n, x), x0, method="COBYLA", options=dict(maxiter=maxiter, rhobeg=0.3))
        nev += r.nfev
        if best is None or r.fun < best.fun:
            best = r
    return sgn * best.fun, best.x, nev


def greedy_local(n, edges, seed=0, restarts=20):
    """Single-flip local search for max-cut from random starts."""
    rng = np.random.default_rng(seed); W = np.zeros((n, n))
    for i, j, w in edges:
        W[i, j] += w; W[j, i] += w
    best = -1
    for _ in range(restarts):
        s = rng.integers(0, 2, n) * 2 - 1
        improved = True
        while improved:
            improved = False
            for i in rng.permutation(n):
                if s[i] * (W[i] @ s) > 0:          # flipping i gains cut weight when same-side weight exceeds cross weight
                    s[i] = -s[i]; improved = True
        best = max(best, 0.25 * np.sum(W * (1 - np.outer(s, s))))
    return best


def spectral(n, edges):
    W = np.zeros((n, n))
    for i, j, w in edges:
        W[i, j] += w; W[j, i] += w
    # max-cut heuristic: sign pattern of the lowest eigenvector of the signless Laplacian D + W (large where neighbours get opposite signs)
    D = np.diag(W.sum(1)); vals, vecs = np.linalg.eigh(D + W)
    s = np.where(vecs[:, 0] >= 0, 1, -1)
    return 0.25 * np.sum(W * (1 - np.outer(s, s)))
