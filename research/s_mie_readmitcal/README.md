# MIE 2027 – ReadmitCal: is a 30-day readmission model for diabetes already calibrated? (real data, independent re-run)

**Data (real):** UCI Diabetes 130-US hospitals 1999–2008 (`diabetic_data.csv`, 101,766 encounters; CC BY 4.0). The file was taken from a public GitHub copy (`Sangha05/Diabetes_Readmission`, byte-identical to `swengzju/Predicting-Diabetes-Patient-Readmission`) because UCI is blocked in this environment.
First encounter per patient, deaths and hospice discharges excluded: **69,990 patients**, readmission < 30 days in 8.98 %.
**Method:** logistic regression and gradient boosting, 60/20/20 patient-level splits, 10 seeds; Platt, isotonic and temperature scaling fitted on the validation part; ECE with 15 bins; subgroup recalibration within three age groups.

| model | AUROC | ECE raw | ECE Platt | ECE isotonic | ECE temperature |
|---|---|---|---|---|---|
| logistic regression | 0.646 ± 0.006 | 0.0053 ± 0.0009 | 0.0058 ± 0.0006 | 0.0066 ± 0.0010 | 0.0063 ± 0.0013 |
| gradient boosting | 0.650 ± 0.004 | 0.0061 ± 0.0013 | 0.0061 ± 0.0009 | 0.0066 ± 0.0007 | 0.0061 ± 0.0009 |

Per-age-group ECE: raw ≈ 0.009, global Platt ≈ 0.009, subgroup Platt ≈ 0.009–0.010; subgroup recalibration did not help. (± = 95 % interval over 10 seeds; full numbers in `results.json`.)
Reproduces the "already calibrated, recalibration does not help" finding; the earlier ECE of about 0.007 is refined to 0.005–0.006.
Not done: temporal validation, subgroups other than age, comparison with published fairness audits.
Run: `python research/s_mie_readmitcal/run.py <path to diabetic_data.csv>` (scikit-learn, scipy, pandas).
