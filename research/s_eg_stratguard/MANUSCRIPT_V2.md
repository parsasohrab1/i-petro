# StratGuard manuscript, version 2 (reframed after the Energy Geoscience desk rejection)

Status: draft for owner decision. Nothing has been submitted. All numbers come from `results.json`, `results_local_cal.json`
and the new `results_net_pay.json` (script `net_pay.py`, real SEG 2016 and FORCE 2020 data, same protocol as the main study).

## Why a v2
Version 1 reported only that conformal coverage fails well by well. A reviewer of a subsurface journal asks "what does this change in a
reservoir decision?". V2 adds one decision-level result, a certified bound on the reservoir fraction of a well, and reports honestly that the
bound is valid but wide. The paper stays a diagnostic/benchmark study; it should go to a venue that publishes such studies, not to an AI-methods special issue.

## Proposed title
How Reliable Are Conformal Facies Sets? Well-by-Well Coverage and Certified Reservoir-Fraction Bounds on SEG 2016 and FORCE 2020 Well Logs

## Proposed abstract (draft, ~230 words)
Machine-learning facies interpretation seldom states how far its answer can be trusted in a given well. We test split conformal prediction on two public log data sets with splits by well: SEG 2016 (Kansas, 10 wells) and FORCE 2020 (North Sea, 81 wells). At a 0.90 target the mean coverage was 0.904 and 0.889, but the worst well reached only 0.735 and 0.599, and 19 of 81 FORCE wells fell below 0.85. Recomputing the threshold from 100 labelled depths of the new well raised worst-well coverage to 0.88 and 0.82 and cut the under-covered FORCE wells to 6, at the price of larger sets. To link the sets to a reservoir decision we derived, for each well, a lower and an upper bound on the reservoir-quality fraction from the sets. The bounds contained the true fraction in 96% of SEG wells and 93% of FORCE wells, but they were wide (mean width 0.69 and 0.38 of the well), and a naive interval (point estimate plus or minus the 0.9 quantile of other wells' errors) reached 89% coverage with clearly narrower widths (0.38 and 0.31). Grammar-constrained decoding removed all impossible contacts without a reliable accuracy gain. Certified sets are therefore valid but not efficient for net-reservoir estimation on these data: a simple error-quantile interval is narrower at similar coverage, and well-local labelling is needed before sets support decisions. Reservoir classes are our assumption; coverage was not assessed per facies class.

## New results subsection (insert after Results 5.x)
**Reservoir-fraction bounds.** For each held-out well, the lower bound is the share of depths whose whole set consists of reservoir classes, and the upper bound is the share whose set contains at least one reservoir class (reservoir classes as in Section 3). The pooled-calibration bound covered the true reservoir fraction in 96.3% of SEG 2016 wells (mean width 0.686) and 92.6% of FORCE 2020 wells (0.381). With 100 locally labelled depths the corresponding numbers were 100% (0.641) and 85.2% (0.438). The base classifier's point estimate had a mean absolute error of 0.102 (3 of 9 wells above 0.10) and 0.072 (17 of 81 wells above 0.10) against true mean reservoir fractions of 0.258 and 0.195. Local labelling therefore did not help the bound on FORCE (one random draw of labelled depths) even though it helped the facies-level coverage.

| | SEG 2016 | FORCE 2020 |
|---|---|---|
| wells analysed | 9 (one 80-sample well excluded, m = 100 labels needed) | 81 |
| true reservoir fraction (mean) | 0.258 | 0.195 |
| point-estimate abs. error | 0.102 | 0.072 |
| pooled bound covers truth | 96.3% | 92.6% |
| pooled bound mean width | 0.686 | 0.381 |
| local (m = 100) bound covers truth | 100% | 85.2% |
| local bound mean width | 0.641 | 0.438 |

## Added limits
- Naive-interval baseline (run 2026-11-06, `net_pay_naive.py`, `results_net_pay_naive.json`): coverage of the true reservoir fraction 0.889 (SEG, 9 wells) and 0.889 (FORCE, 81 wells), mean width 0.383 and 0.306, versus conformal-derived bound 0.963/0.686 and 0.926/0.381. The conformal-derived bound over-covers and is wider; the naive interval is the more efficient one at about the nominal 0.90. This is a negative finding for the certified bound and is reported as such. The naive interval uses leave-one-well-out errors, which needs a fleet of labelled wells.
- Reservoir classes are an assumption; the local-calibration experiment used one random draw on FORCE.
- The two SEG and FORCE results are not comparable across data sets (different label sets).

## Contribution list (replace)
(i) a per-well coverage analysis of conformal facies sets on two public data sets; (ii) a measured, negative-to-modest evaluation of grammar decoding and referral; (iii) well-local recalibration with its gain and cost; (iv) a certified reservoir-fraction bound, shown to be valid but less efficient than a naive error-quantile interval.

## Venue shortlist (not verified; each needs the venue-fit gate and an enquiry first)
Choose a journal whose scope accepts benchmark/diagnostic studies with public data and code. Candidates to check against their current scope pages and recent papers: Computers & Geosciences; Artificial Intelligence in Geosciences (KeAi); Geoenergy Science and Engineering (already in the dashboard list). I could not read these scope pages from this session, so fit is not established.

## Before any submission
1. Done: naive-interval baseline (see Added limits).
2. Put the code in a public archive (owner and patent-attorney approval first); "on request" is a weakness.
3. Complete `docs/VENUE_FIT_GATE.md` for the chosen journal and send an enquiry.
