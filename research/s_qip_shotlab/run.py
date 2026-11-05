"""python -m research.s_qip_shotlab.run -> results.json   (Hamiltonians computed with PySCF, state = exact ground state; no hardware data)"""
import json, time
import numpy as np
from . import ham, shots

CASES = [("H2", "H 0 0 0; H 0 0 0.74", [10 ** 3, 10 ** 4, 10 ** 5]), ("LiH", "Li 0 0 0; H 0 0 1.6", [10 ** 4, 10 ** 5, 10 ** 6])]


if __name__ == "__main__":
    out = []
    for name, atom, totals in CASES:
        op, mf, N, ne = ham.molecule(atom); terms, const, qop = ham.pauli_terms(op, N)
        e0, psi = ham.ground_state(qop, N)
        ce = shots.term_expectations(qop, psi, N)
        tl = [(float(np.real(c)), t) for t, c in qop.terms.items() if t]
        res = dict(mol=name, qubits=N, pauli_terms=len(terms), e_ground=e0, n_terms_nonzero_expectation=int(np.sum(np.abs(ce[:, 1]) > 1e-9)), budgets={})
        for T in totals:
            row = {k: float(np.sqrt(shots.alloc_variance(ce, w, T))) for k, w in shots.allocations(ce).items()}      # RMSE (unbiased, so = SD) in Ha
            res["budgets"][str(T)] = dict(rmse_Ha=row, rel_to_uniform={k: v / row["uniform"] for k, v in row.items()})
        t0 = time.time(); Ts = totals[0] if name == "LiH" else totals[1]
        v, m = shots.shadow_variance_mc(psi, N, tl, Ts, reps=60 if name == "LiH" else 200, seed=3)
        sh = dict(budget=Ts, rmse_Ha=float(np.sqrt(v + (m - (e0 - const)) ** 2)), bias_Ha=float(m - (e0 - const)), seconds=time.time() - t0)
        sh["rel_to_uniform_same_budget"] = sh["rmse_Ha"] / res["budgets"][str(Ts)]["rmse_Ha"]["uniform"]
        res["shadows"] = sh
        out.append(res); print(json.dumps(res, indent=1))
    json.dump(out, open("research/s_qip_shotlab/results.json", "w"), indent=1)
