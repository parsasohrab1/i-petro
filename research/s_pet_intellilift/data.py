import pathlib
import numpy as np
import pandas as pd

SENSORS = ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP", "P-JUS-CKGL", "QGL"]


def well_of(name):
    return pathlib.Path(name).name.split("_")[0]          # WELL-00001


def load_real(root, step=60, min_valid=0.5):
    """Real 3W instances (WELL-*.parquet): returns list of dicts {well, cls, x (T,d) at 1/step Hz, y (T,) class codes (0 normal), onset}.
    Sensors that are mostly missing in an instance are NaN columns (ignored by the statistic)."""
    out = []
    for f in sorted(pathlib.Path(root).glob("[0-9]/WELL-*.parquet")):
        d = pd.read_parquet(f, columns=SENSORS + ["class"]).iloc[::step]
        y = d["class"].astype("float").fillna(-1).to_numpy().astype(int)
        x = d[SENSORS].to_numpy(float).copy()
        x[:, np.isnan(x).mean(0) > 1 - min_valid] = np.nan
        cls = int(f.parent.name)
        onset = None
        if cls:
            nz = np.flatnonzero((y > 0) & (y < 100)); nz = nz if len(nz) else np.flatnonzero(y > 0)
            onset = int(nz[0]) if len(nz) else None
        out.append(dict(well=well_of(f.name), cls=cls, x=x, y=y, onset=onset))
    return out
