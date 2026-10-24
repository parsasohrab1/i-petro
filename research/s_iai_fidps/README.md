# FIDPS – log zonation by change-point segmentation (private research notes)

Data: FORCE 2020 lithology competition training wells (62 wells with usable GROUP labels and logs; GR, RHOB, NPHI, DTC; every 10th sample). Ground truth = stratigraphic GROUP boundaries (mean 5.0 per well) – a surrogate for zonation; **not formation-damage data**.
Methods: PELT (ruptures, l2 cost) vs smoothed-gradient peak baseline; one parameter each tuned on half of the wells (5 random half/half splits by well), micro-averaged boundary F1 on the other half, tolerance 15 m. Random boundaries with the true count as reference.
Run (~25 min): `python -m research.s_iai_fidps.run <train.csv>`. Tests: synthetic step series.

## Results (test F1, mean +- SD over 5 splits)
PELT 0.331 +- 0.009 (9.3 boundaries per well) | gradient 0.303 +- 0.011 (13.3) | random 0.091.
PELT is ahead of the baseline by 0.03 F1 – small; the SD only reflects the choice of wells in overlapping splits, not a significance test. Both over-segment (9–13 vs 5 true boundaries per well); precision is the weak point. On SEG 2016 (owner's earlier run) the baseline was better (0.62 vs 0.55), so the ranking depends on the data set.
