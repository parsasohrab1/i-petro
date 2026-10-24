"""Leave-one-failure-out evaluation of the RUL lower bound on the four documented NASA IMS bearing failures."""
import numpy as np
import pandas as pd

from . import ims, rul

FINAL_H, ALERT_H = 48.0, 48.0


def metrics(d, pred):
    """unsafe = predicted RUL above the true RUL (an overestimate).
    unsafe_final: share of the last FINAL_H hours with an overestimate. false_alert: share of snapshots whose prediction is <= ALERT_H while the
    true RUL is more than 4 x ALERT_H. first_alert_true_rul: true remaining life at the first snapshot predicted <= ALERT_H (0 = never alerted)."""
    true = d.rul.to_numpy()
    hit = np.where(pred <= ALERT_H)[0]
    return {"unsafe_all": float((pred > true).mean()), "unsafe_final": float((pred > true)[true <= FINAL_H].mean()),
            "false_alert": float(((pred <= ALERT_H) & (true > 4 * ALERT_H)).mean()), "first_alert_true_rul": float(true[hit[0]]) if len(hit) else 0.0}


def run(folder, alpha=0.1, model_cls=rul.HIRegressor, series=None):
    series = series or {k: ims.load_bearing(folder, *k) for k in ims.FAILED}
    rows = []
    for held, d in series.items():
        train = [s for k, s in series.items() if k != held]
        pt = model_cls().fit(train).predict(d)
        q = rul.overestimation_quantile(model_cls, train, alpha)
        for name, pred in (("constant_life", rul.ConstantLife().fit(train).predict(d)), ("point", pt), ("lower_bound", rul.lower_bound(pt, q))):
            rows.append({"held_out": f"{held[0]}-B{held[1]}", "life_h": float(d.t.iloc[-1]), "method": name, "q_hours": q if name == "lower_bound" else np.nan, **metrics(d, pred)})
    return pd.DataFrame(rows)


def summary(r):
    return r.groupby("method")[["unsafe_all", "unsafe_final", "false_alert", "first_alert_true_rul"]].mean().round(3)
