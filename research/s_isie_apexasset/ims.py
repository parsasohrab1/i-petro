"""Loading of the NASA IMS run-to-failure feature tables (Hora & Rezapour, MIT licence; raw data: Lee et al. 2007, IMS, University of Cincinnati).

Not part of the product's claimed functions: this add-on only post-processes a remaining-useful-life estimate.
"""
import numpy as np
import pandas as pd

FAILED = [("T1", 3), ("T1", 4), ("T2", 1), ("T3", 3)]      # documented failures of the IMS experiments
FILES = {"T1": "test1_features.csv", "T2": "test2_features.csv", "T3": "test3_features.csv"}


def operating_hours(ts):
    """Cumulative operating time: gaps longer than 15 min (experiment paused) count as one 10-min interval, as in the data documentation."""
    t = pd.to_datetime(pd.Series(ts)).reset_index(drop=True)
    dt = t.diff().dt.total_seconds().fillna(0) / 3600
    dt = np.where(dt > 0.25, 10 / 60, dt)
    return np.cumsum(dt)


def load_bearing(folder, run, bearing):
    d = pd.read_csv(f"{folder}/{FILES[run]}", parse_dates=["timestamp"])
    d = d[d.bearing == bearing].groupby("timestamp", as_index=False)[["rms", "kurtosis_pearson", "peak2peak"]].mean().sort_values("timestamp")
    d["t"] = operating_hours(d.timestamp)
    d["rul"] = d.t.iloc[-1] - d.t              # the file ends at failure
    return d.reset_index(drop=True)
