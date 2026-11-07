# StretchWatch – HF reference quality along stretching curves, checked against PySCF FCI/CCSD (private research notes)

Computed (not measured) Hamiltonians, PySCF 2.14. Molecules: H2, LiH, BeH2 (linear, symmetric stretch), H2O (symmetric OH stretch, 104.5 deg); STO-3G, plus LiH in 6-31G. Per geometry: RHF, FCI, CCSD, CCSD(T), squared overlap of the HF determinant with the FCI ground state (|c0|^2), natural-orbital occupation entropy of the FCI 1-RDM.
Run: `python -m research.s_icqe_stretchwatch.run`. Tests: H2 vs literature (-1.1373 Ha), entropy limits.

## Results
- H2 at 0.74 A: FCI -1.1373 Ha, |c0|^2 = 0.987 (matches the literature value).
- |c0|^2 falls with stretching: H2 0.987 -> 0.504 (4 A); LiH 0.982 (1.0 A) -> 0.556 (4 A); BeH2 0.982 -> 0.382 (3.5 A); H2O 0.987 -> 0.362 (2.2 A). LiH 6-31G: 0.979 -> 0.507 (4 A).
- Within each molecule the overlap and the entropy are almost perfectly rank-anti-correlated (Spearman -0.99 to -1.0): the two ingredients of the index carry nearly the same information, so combining them adds little.
- CCSD(T) reproduces FCI to < 1 mHa for H2, LiH (up to 4 A), H2O (<= 1.7 A), BeH2 (<= 2.5 A); it fails (errors 9 to 30 mHa) beyond that, as expected.
- 5 points are flagged `scf_suspect` (LiH 6 and 8 A STO-3G, LiH 8 A 6-31G, BeH2 5 A, H2O 3 A): the restricted HF converged to a high-energy ionic solution or CCSD failed, HF-FCI > 400 mHa and not reproducible between runs. The earlier LiH overlap of 0.008 at 8 A is of this type and is not a clean property of the molecule. They are excluded from the correlations.
