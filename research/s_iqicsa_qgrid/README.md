# QGrid-Part – QAOA vs classical for splitting real power-system networks (private research notes)

Data: IEEE/MATPOWER cases bundled with the PyPI package `pandapower` (case9, case14: topology, loads, generation); an AC power flow gives the branch flows used as weights.
Objectives: (A) weighted MaxCut on |P| flow (as in the abstract); (B) islanding: minimise flow cut + |net injection of one island| (MW), each island >= 3 buses.
Exact state-vector QAOA, p = 1..3, COBYLA, 5 random restarts (max 300 iterations each). Baselines: greedy single-flip search (20 restarts), spectral heuristic, exhaustive optimum (2^n). Limit: statevector memory (n <= ~24; case30 needs 2^30 amplitudes – not run).
Run: `python -m research.s_iqicsa_qgrid.run`. Tests: synthetic graphs only.

## Results
| | case9 | case14 |
|---|---|---|
| MaxCut ratio, greedy / spectral | 1.00 / 1.00 | 1.00 / 0.62 |
| MaxCut ratio, QAOA p=1,2,3 | 0.742, 0.797, 0.714 | 0.760, 0.820, 0.753 |
| P(optimum) QAOA p=2 | 0.149 | 0.0037 |
| Islanding: QAOA score (0 = random, 1 = optimum) p=1,2,3 | 0.31, 0.16, 0.22 | 0.14, 0.18, 0.10 |
| Islanding: local descent gap to optimum | 0 | 0 |

QAOA is not better than greedy search, and p=3 is worse than p=2, i.e. the classical optimiser, not the depth, is the limit here (not monotone in p). For islanding, QAOA's expected cost is far from the optimum while single-flip descent finds it.
