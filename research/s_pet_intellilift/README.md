# IntelliLift – conformal alarm thresholds on the real Petrobras 3W data (private research notes)

Data: Petrobras 3W v2.0.0 (github.com/petrobras/3W, CC BY 4.0), real instances only (`WELL-*.parquet`): 1119 instances from 40 wells,
594 normal (class 0) and 525 faults (classes 1–9: 4, 22, 32, 343, 11, 6, 36, 14, 57). Sensors: P-PDG, P-TPT, T-TPT, P-MON-CKP, T-JUS-CKP, P-JUS-CKGL, QGL, 1-min sampling.

Method: reference = first 30 min of each instance (labelled normal); statistic = max over sensors of robust |z| (rolling median 5 min);
threshold = conformal quantile (alpha = 0.1) of per-instance maxima over normal calibration instances; **wells are split** (half calibration, half test), 20 random splits.
Baselines: fixed thresholds z = 5, 10, 20 (no calibration). Run: `python -m research.s_pet_intellilift.run <dataset dir>`. Tests use synthetic series only.

## Results (alpha = 0.1)
- False-alarm rate on held-out normal instances: **0.147 mean, SD 0.171**, 5–95 % range 0.009–0.551 over splits; above 0.10 in 50 % of splits. Fixed z = 5/10/20: 0.195 / 0.103 / 0.067.
  The instance-level guarantee does not carry over to new wells: instances of one well are not exchangeable with instances of others.
- Alarm from the labelled onset on (conformal threshold), share of held-out fault instances: class 1 0.35, 2 0.96, 3 0.47, 4 (n≈171) **0.09**, 5 0.74, 6 0.21, 7 0.42, 8 0.87, 9 0.61.
- Alarms *before* the labelled onset occur in 4–86 % of fault instances; the pre-onset part is labelled normal, so these cannot be separated from false alarms and are not counted as early warning.
- Weak point: class 4 (largest, 343 instances) is almost invisible to these 7 sensors.
