# ICMHI 2027 – IPIND: conformal coverage under chemical-component shift (real data, independent re-run)

**Data (real):** AGILE library, 1,199 ionisable lipids built from amine (A), aldehyde (B) and isocyanide (C) components, with experimental HeLa transfection values
(`bowang-lab/AGILE`, file `AGILE_smiles_with_value_group.csv`). **Method:** random forest on Morgan count fingerprints (radius 2, 1,024 bits), split conformal intervals, nominal coverage 0.90, 60/20/20 splits, 10 seeds; random split versus splits by whole component groups.

| split | mean coverage | 95 % CI | min – max over seeds | interval width |
|---|---|---|---|---|
| random | 0.915 | ±0.021 | 0.842 – 0.958 | 8.06 |
| by A component | 0.921 | ±0.035 | 0.821 – 0.992 | 10.14 |
| by B component | 0.840 | ±0.082 | 0.577 – 0.977 | 9.08 |
| by C component | 0.865 | ±0.063 | 0.617 – 0.975 | 8.75 |

**Honest note:** this independent run does **not** reproduce the coverage of 0.72 quoted in the current abstract (owner's earlier run, ~1,100 lipids, series definition and model not recorded). Under component-group shift coverage here falls to 0.84–0.87 on average and to 0.58–0.62 in the worst split, with wide variation between splits. The abstract should state these numbers, or the original protocol must be recovered and re-run.
Run: `python research/s_icmhi_ipind/run.py <path to AGILE_smiles_with_value_group.csv>` (needs rdkit, scikit-learn).
