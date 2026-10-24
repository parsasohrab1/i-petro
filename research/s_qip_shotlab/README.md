# Shot-Budget Lab – allocation of shots over Pauli terms, molecular Hamiltonians (private research notes)

Computed (not measured) Hamiltonians: PySCF integrals -> OpenFermion Jordan-Wigner; STO-3G; H2 at 0.74 A (4 qubits, 14 Pauli terms) and LiH at 1.6 A (12 qubits, 630 terms); state = exact ground state (energies -1.1373 and -7.8823 Ha, equal to FCI).
No grouping of commuting terms; one term per shot. Uniform / weighted by |c| / oracle |c|*sigma (needs the unknown state; reference only): exact analytic variance (the estimators are unbiased, so RMSE = SD). Classical shadows (random local Pauli): Monte-Carlo, 200 repeats (H2, 10^4 snapshots) and 60 repeats (LiH, 10^4 snapshots), so the shadow numbers are noisy (LiH bias 0.025 Ha ~ 1 SE).
Run: `python -m research.s_qip_shotlab.run` (~15 min, shadows dominate). Tests: toy 2-qubit cases.

## RMSE relative to uniform allocation (same total shots)
| | H2 | LiH |
|---|---|---|
| weighted by \|c\| | **1.35** (worse) | 0.86 (14 % lower) |
| oracle \|c\|sigma | 0.75 | 0.57 |
| classical shadows | **3.05** (worse) | **3.14** (worse) |
Absolute RMSE at 10^6 shots: LiH uniform 6.9 mHa, weighted 5.9 mHa, oracle 3.9 mHa; chemical accuracy (1.6 mHa) is not reached by any scheme without grouping.
The ratios are independent of the budget (RMSE ~ 1/sqrt(shots)).
