"""Shot-allocation study for Pauli-sum expectation values: analytic variance for term-wise allocations and Monte-Carlo classical shadows (returns variance and mean of the repeated estimates)."""
import numpy as np
import openfermion as of


def term_expectations(qop, psi, N):
    out = []
    for t, c in qop.terms.items():
        if not t: continue
        P = of.get_sparse_operator(of.QubitOperator(t, 1.0), n_qubits=N)
        out.append((float(np.real(c)), float(np.real(np.vdot(psi, P @ psi)))))
    return np.array(out)                     # columns: coefficient, <P>


def alloc_variance(ce, weights, total):
    """Variance of the sum_i c_i * mean(shots_i) estimator with n_i = total * w_i / sum(w) shots (continuous allocation)."""
    c, e = ce[:, 0], ce[:, 1]; w = np.asarray(weights, float); n = total * w / w.sum()
    return float(np.sum(c ** 2 * (1 - e ** 2) / n))


def allocations(ce):
    c, e = ce[:, 0], ce[:, 1]
    return dict(uniform=np.ones(len(c)), weighted_abs_c=np.abs(c), oracle_abs_c_sigma=np.abs(c) * np.sqrt(np.maximum(1 - e ** 2, 1e-12)))


def shadow_variance_mc(psi, N, ce_terms, total, reps=200, seed=0):
    """Random local-Pauli classical shadows: empirical variance over `reps` repeats of the estimate of sum_i c_i <P_i>, each with `total` snapshots."""
    rng = np.random.default_rng(seed)
    # terms as arrays: basis[q] in {0:none,1:X,2:Y,3:Z}
    B = np.zeros((len(ce_terms), N), int)
    C = np.array([c for c, _ in ce_terms])
    for k, (c, t) in enumerate(ce_terms):
        for q, p in t: B[k, q] = "XYZ".index(p) + 1
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    ests = []
    T = total
    for _ in range(reps):
        bases = rng.integers(1, 4, (T, N))
        # sample outcomes: for speed group snapshots by identical basis rows is impossible; rotate each snapshot
        outs = np.empty((T, N), int)
        for s in range(T):
            psi_r = psi.reshape((2,) * N)
            for q in range(N):
                b = bases[s, q]
                if b == 3: continue
                U = H if b == 1 else H @ np.diag([1, -1j])          # X: H; Y: H S^dagger
                # OpenFermion: qubit 0 is the most significant bit, i.e. axis q of the reshaped state
                psi_r = np.moveaxis(np.tensordot(U, psi_r, axes=([1], [q])), 0, q)
            p = np.abs(psi_r.reshape(-1)) ** 2; p /= p.sum()
            k = rng.choice(len(p), p=p)
            outs[s] = [(k >> (N - 1 - q)) & 1 for q in range(N)]
        sgn = 1 - 2 * outs
        est = 0.0
        for k in range(len(C)):
            m = B[k] > 0
            match = np.all((bases[:, m] == B[k, m]), axis=1)
            val = np.where(match, 3.0 ** m.sum() * np.prod(sgn[:, m], axis=1), 0.0)
            est += C[k] * val.mean()
        ests.append(est)
    return float(np.var(ests, ddof=1)), float(np.mean(ests))
