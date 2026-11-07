"""Molecular qubit Hamiltonians (Jordan-Wigner) from PySCF integrals via OpenFermion, as dense Pauli lists."""
import numpy as np
import openfermion as of
from pyscf import gto, scf, ao2mo
from scipy.sparse.linalg import eigsh


def molecule(atom, basis="sto-3g", frozen_core=0):
    mol = gto.M(atom=atom, basis=basis, verbose=0); mf = scf.RHF(mol); mf.kernel()
    C = mf.mo_coeff; n = C.shape[1]
    h1 = C.T @ mf.get_hcore() @ C; eri = ao2mo.restore(1, ao2mo.kernel(mol, C), n)
    core = list(range(frozen_core)); act = list(range(frozen_core, n))
    e_core = mol.energy_nuc() + 2 * sum(h1[i, i] for i in core) + sum(2 * eri[i, i, j, j] - eri[i, j, j, i] for i in core for j in core)
    h = h1[np.ix_(act, act)] + sum(2 * eri[np.ix_(act, act, [i], [i])][:, :, 0, 0] - eri[np.ix_(act, [i], [i], act)][:, 0, 0, :] for i in core) if core else h1
    g = eri[np.ix_(act, act, act, act)]
    m = len(act); N = 2 * m
    T1 = np.zeros((N, N)); T2 = np.zeros((N, N, N, N))
    for p in range(m):
        for q in range(m):
            for s in (0, 1):
                T1[2 * p + s, 2 * q + s] = h[p, q]
    for p in range(m):
        for q in range(m):
            for r in range(m):
                for t in range(m):
                    for s1 in (0, 1):
                        for s2 in (0, 1):
                            # H2 = 1/2 sum (pq|rt) a+_{p s1} a+_{r s2} a_{t s2} a_{q s1}  ->  OpenFermion tensor index [p,r,t,q]
                            T2[2 * p + s1, 2 * r + s2, 2 * t + s2, 2 * q + s1] += 0.5 * g[p, q, r, t]
    return of.InteractionOperator(float(e_core), T1, T2), mf, N, mol.nelectron - 2 * len(core)


def pauli_terms(op, N):
    """-> list of (coefficient, x_mask, z_mask) excluding the identity, and the identity constant."""
    qop = of.jordan_wigner(op); terms = []; const = 0.0
    for t, c in qop.terms.items():
        c = float(np.real(c))
        if not t:
            const += c; continue
        x = z = 0
        for q, p in t:
            if p in ("X", "Y"): x |= 1 << q
            if p in ("Z", "Y"): z |= 1 << q
        terms.append((c, x, z, t))
    return terms, const, qop


def ground_state(qop, N):
    H = of.get_sparse_operator(qop, n_qubits=N)
    w, v = eigsh(H, k=1, which="SA")
    return float(w[0]), v[:, 0]
