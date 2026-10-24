# ISIE 2027 – ApexAsset AI: conservative RUL lower bound on real run-to-failure data

**Data (real):** NASA IMS bearing run-to-failure experiments (Lee et al. 2007, IMS, University of Cincinnati). The per-snapshot feature tables used here come from the public
GitHub repository `bhavjeetsinghh/ims-bearing-label-free-early-warning` (MIT licence, citation required: Hora & Rezapour). The raw NASA files could not be downloaded
(the environment's network policy blocks NASA hosts); the feature tables are derived from them by the repository's `extract_features.py`.
Four documented failures: Test 1 bearings 3 and 4, Test 2 bearing 1, Test 3 bearing 3 (lives 345, 345, 164 and 1053 operating hours).

**Add-on (separate from the product's claimed functions):** a lower bound on the remaining useful life = point estimate − the (1−α) quantile of its past overestimation errors,
measured by inner leave-one-bearing-out prediction on the training bearings. The point estimate here is a monotone (isotonic) map of a smoothed log-RMS health index; the add-on works with any estimator.

**Validation:** leave-one-failure-out (train on three failures, test on the fourth), baselines: constant life, uncorrected estimate. `python -m pytest research/s_isie_apexasset`; results in `results.json`.
Synthetic series are used only in the unit tests.

| 4 held-out failures (mean) | overestimates in last 48 h | overestimates over the whole life | false alerts (alert ≤ 48 h while > 192 h remain) |
|---|---|---|---|
| constant life | 75 % | 75 % | 15 % |
| point estimate | 66 % | 48 % | 0 % |
| lower bound, α = 0.1 | **0 %** (all four failures) | 18 % (T2-B1: 55 %) | 23 % (T3-B3: 81 %) |
| lower bound, α = 0.2 | 37 % | 39 % | 0 % |

Limits: four failures only, one vibration feature, one estimator; the 10 % target is not met over the whole life, and the bound is conservative (quantile 115–184 h against lives of 164–1053 h).
Not done: a second run-to-failure data set (NASA battery data and FEMTO/PRONOSTIA are on blocked hosts), learned RUL models, statistical tests.
