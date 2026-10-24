import numpy as np
import pandas as pd

SEG_LOGS = ["GR", "ILD_log10", "DeltaPHI", "PHIND", "PE", "NM_M", "RELPOS"]
SEG_RESERVOIR = (1, 8, 9)            # assumption: non-marine sandstone, packstone-grainstone, phylloid-algal bafflestone count as reservoir-quality
FORCE_LOGS = ["GR", "RHOB", "NPHI", "RDEP", "DTC", "PEF", "CALI"]
FORCE_RESERVOIR = (30000, 70000, 74000, 70032)    # sandstone, limestone, dolomite, chalk


def load_seg(path):
    d = pd.read_csv(path).sort_values(["Well Name", "Depth"]).reset_index(drop=True)
    return d[SEG_LOGS].to_numpy(float), d["Facies"].to_numpy(int), d["Well Name"].to_numpy()


def load_force(path, step=10, min_rows=400):
    """FORCE 2020 training wells; every `step`-th sample (labels change slowly with depth); log10 of the deep resistivity."""
    d = pd.read_csv(path, sep=";", usecols=["WELL", "DEPTH_MD"] + FORCE_LOGS + ["FORCE_2020_LITHOFACIES_LITHOLOGY"])
    d = d.sort_values(["WELL", "DEPTH_MD"]); d = d[d.groupby("WELL").cumcount() % step == 0]
    d["RDEP"] = np.log10(d["RDEP"].clip(lower=1e-3))
    vc = d.WELL.value_counts(); d = d[d.WELL.isin(vc[vc >= min_rows].index)]
    return d[FORCE_LOGS].to_numpy(float), d["FORCE_2020_LITHOFACIES_LITHOLOGY"].to_numpy(int), d["WELL"].to_numpy()
