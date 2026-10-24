"""python -m research.s_iqicsa_qgrid.run  -> results.json  (networks bundled with the pandapower package: MATPOWER/IEEE cases)"""
import json
import numpy as np
from . import qaoa, grid


def island_cost(n, edges, inj, lam=1.0, min_side=3):
    """minimise: power flow cut by the split + lam * |net injection of one side| (MW), each island has at least min_side buses."""
    b = qaoa.bits(n); cut = qaoa.maxcut_diag(n, edges)
    imb = np.abs(b @ inj)
    c = cut + lam * imb
    sz = b.sum(1); c[(sz < min_side) | (sz > n - min_side)] = c.max() * 2 + 1
    return c


def local_descent(diag, n, seed, restarts=30):
    rng = np.random.default_rng(seed); best = np.inf
    for _ in range(restarts):
        x = int(rng.integers(0, 2 ** n))
        while True:
            nb = [x ^ (1 << i) for i in range(n)]; y = nb[int(np.argmin(diag[nb]))]
            if diag[y] < diag[x]: x = y
            else: break
        best = min(best, diag[x])
    return float(best)


def score(v, lo, hi, maximise):
    return float((v - lo) / (hi - lo)) if maximise else float((hi - v) / (hi - lo))


def run(name, ps=(1, 2, 3), restarts=5):
    n, edges, inj = grid.load(name)
    out = dict(case=name, n_buses=n, n_branches=len(edges), total_gen_MW=float(inj[inj > 0].sum()))
    d1 = qaoa.maxcut_diag(n, edges)
    out["maxcut"] = dict(opt=float(d1.max()), mean_random=float(d1.mean()),
                         greedy=qaoa.greedy_local(n, edges) / d1.max(), spectral=qaoa.spectral(n, edges) / d1.max(), qaoa={})
    for p in ps:
        v, x, nev = qaoa.optimise(d1, n, p, restarts=restarts, seed=p)
        psi = qaoa.state(d1, n, x[:p], x[p:]); prob_opt = float(np.sum(np.abs(psi[d1 >= d1.max() - 1e-9]) ** 2))
        out["maxcut"]["qaoa"][str(p)] = dict(ratio=float(v / d1.max()), prob_optimum=prob_opt, evaluations=int(nev))
    d2 = island_cost(n, edges, inj); lo, hi = float(d2.min()), float(d2.mean())
    out["islanding"] = dict(opt=lo, mean_random=hi, local_descent_gap=float(local_descent(d2, n, 0) - lo), qaoa={})
    for p in ps:
        v, x, nev = qaoa.optimise(d2, n, p, restarts=restarts, seed=10 + p, maximise=False)
        psi = qaoa.state(d2, n, x[:p], x[p:]); prob_opt = float(np.sum(np.abs(psi[d2 <= lo + 1e-9]) ** 2))
        out["islanding"]["qaoa"][str(p)] = dict(expected_cost=float(v), score=score(v, lo, hi, False), prob_optimum=prob_opt, evaluations=int(nev))
    return out


if __name__ == "__main__":
    res = [run(c) for c in ("case9", "case14")]
    json.dump(res, open("research/s_iqicsa_qgrid/results.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
