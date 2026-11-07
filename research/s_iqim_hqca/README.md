# IQIM 2027 – HQCA: uncertainty intervals for binding-affinity predictions, second real target (EGFR)

**Data (real):** EGFR IC50 values from ChEMBL 25 (3 884 structures, pIC50 1.6–11.4; 1 444 Bemis–Murcko scaffolds), taken from the TeachOpenCADD talktorial data on GitHub
(`volkamerlab/teachopencadd`, CC BY 4.0; ChEMBL itself is CC BY-SA 3.0). ChEMBL's own servers are blocked in this environment, so the GitHub copy was used. The COX-2 numbers in the abstract (4 392 molecules)
come from the owner's earlier run on their own machine and were not reproduced here.

**Method:** black-box affinity predictor (random forest on Morgan fingerprints, 200 trees) + split conformal intervals; global quantile versus Mondrian (one quantile per tercile of the predicted value).
Splits 60/20/20, either random or by scaffold group (chemical-series shift), 10 seeds, 95 % t-intervals over seeds, nominal coverage 0.90. Synthetic data appear only in the unit tests.

**Result (mean ± 95 % CI over 10 seeds):**

| split | method | coverage (by predicted tercile) | worst predicted tercile | worst true-activity group | interval width (pIC50) |
|---|---|---|---|---|---|
| random | global | 0.896 ± 0.009 | 0.868 ± 0.013 | 0.831 ± 0.012 | 2.76 |
| random | Mondrian | 0.895 ± 0.010 | 0.870 ± 0.011 | 0.837 ± 0.013 | 2.78 |
| scaffold | global | 0.894 ± 0.014 | 0.863 ± 0.019 | 0.783 ± 0.032 | 3.26 |
| scaffold | Mondrian | 0.891 ± 0.016 | 0.851 ± 0.026 | 0.785 ± 0.030 | 3.25 |

The marginal guarantee holds under chemical-series shift; Mondrian stratification by predicted value gives no measurable gain; coverage conditional on the true activity is lower (potency groups), which marginal conformal intervals do not promise.
Not done: the platform's own quantum–classical predictor (not part of this module), a third target, other fingerprints or models.
Run: `python -m pytest research/s_iqim_hqca` (unit tests); the experiment is `egfr.experiment` (see `results.json`).
