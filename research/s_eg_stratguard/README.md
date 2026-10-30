# StratGuard – real-data validation (private research notes)

Data (all public, downloaded from GitHub mirrors; licences to be verified before publication):
- SEG 2016 ML contest, Hugoton/Panoma, 10 wells, 4149 samples, 9 facies (`facies_vectors.csv`).
- FORCE 2020 lithology competition training set, 81 wells (every 10th sample), lithology codes (`train.csv`).

Protocol: wells are split into train / calibration / test (no well shared), HistGradientBoosting, split conformal (LAC), leave-wells-out repeated; stratigraphic transition grammar learnt on training wells, Viterbi decoding; referral = sets larger than 1 (plain) or larger than 1 near reservoir/non-reservoir boundaries (cost-aware).

Run: `python -m research.s_eg_stratguard.run <seg csv> <force train.csv>` → `results.json`. Unit tests use synthetic fixtures only.

## Measured results (target coverage 0.90)
| | SEG 2016 | FORCE 2020 |
|---|---|---|
| wells | 10 | 81 |
| mean coverage | 0.904 | 0.889 |
| worst-well coverage | 0.735 | 0.599 |
| wells below 0.85 | 1 | 19 |
| mean set size | 3.33 | 2.02 |
| accuracy base → decoded | 0.531 → 0.547 | 0.689 → 0.666 |
| grammar violations base → decoded | 80 → 0 | 726 → 0 |
| referral plain (acc. on kept) | 0.889 (0.572) | 0.616 (0.855) |
| referral cost-aware (acc. on kept) | 0.831 (0.574) | 0.408 (0.796) |

Honest reading: marginal coverage holds, per-well coverage does not (19/81 FORCE wells under 0.85). Decoding removes all impossible transitions but does not raise accuracy on FORCE (−2.3 pp). On SEG 2016 sets are so large that referral flags ~89 % of depths – not usable there.

## Few-shot well-local recalibration (new contribution)

`local_cal.py`, results in `results_local_cal.json` (SEG 2016: 8 wells with at least 50 samples, 3 seeds; FORCE 2020: 81 wells, 1 seed; nominal coverage 0.90; m depths of the new well are labelled at random).

| data | calibration | worst-well coverage | wells below 0.85 | mean set size |
|---|---|---|---|---|
| FORCE 2020 | pooled wells only | 0.599 | 19 / 81 | 2.02 |
| FORCE 2020 | local, m = 100 | 0.818 | 6 / 81 | 2.27 |
| SEG 2016 | pooled wells only | 0.803 | 2 / 8 | 4.33 |
| SEG 2016 | local, m = 100 | 0.870 | 0 / 8 | 4.04 |

Caveat: the labelled depths are drawn at random inside the new well, so calibration and test depths of that well are exchangeable; contiguous labelling of the top of a well would be harsher and was not tested. Mixing the pooled scores with the local ones (5x weight) helped much less than local-only.
