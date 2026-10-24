"""EGFR (ChEMBL) data loading, fingerprints, random and scaffold splits, and the experiment."""
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import RandomForestRegressor

from . import affinity_conformal as ac

RDLogger.DisableLog("rdApp.*")


def load(path):
    d = pd.read_csv(path)
    d = d.rename(columns={"canonical_smiles": "smiles"})[["smiles", "pIC50"]].dropna()
    return d.groupby("smiles", as_index=False).pIC50.mean()                    # one value per structure (mean of duplicates)


def featurise(smiles, radius=2, n_bits=2048):
    X, scaf, keep = [], [], []
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s)
        if m is None:
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(m, radius, nBits=n_bits)
        X.append(np.array(fp, dtype=np.uint8)); scaf.append(MurckoScaffold.MurckoScaffoldSmiles(mol=m)); keep.append(i)
    return np.array(X), np.array(scaf), np.array(keep)


def random_split(n, rng, f=(0.6, 0.2)):
    p = rng.permutation(n); a, b = int(f[0] * n), int((f[0] + f[1]) * n)
    return p[:a], p[a:b], p[b:]


def scaffold_split(scaf, rng, f=(0.6, 0.2)):
    """Whole scaffold groups go to one part (chemical-series shift); group order is random."""
    groups = pd.Series(np.arange(len(scaf))).groupby(scaf).apply(list)
    order = rng.permutation(len(groups)); n = len(scaf)
    tr, ca, te = [], [], []
    for gi in order:
        idx = groups.iloc[gi]
        (tr if len(tr) < f[0] * n else ca if len(ca) < f[1] * n else te).extend(idx)
    return np.array(tr, dtype=int), np.array(ca, dtype=int), np.array(te, dtype=int)


def experiment(X, y, scaf, seeds=10, alpha=0.1, n_trees=200):
    rows = []
    for split in ("random", "scaffold"):
        for seed in range(seeds):
            rng = np.random.default_rng(seed)
            tr, ca, te = random_split(len(y), rng) if split == "random" else scaffold_split(scaf, rng)
            rf = RandomForestRegressor(n_trees, min_samples_leaf=2, n_jobs=-1, random_state=seed).fit(X[tr], y[tr])
            pc, pt = rf.predict(X[ca]), rf.predict(X[te])
            act = np.digitize(y[te], [6.0, 8.0])                                  # strata of the TRUE activity: weak, medium, potent
            for mode in ("global", "mondrian"):
                iv = ac.Intervals(alpha, mode).fit(pc, y[ca])
                hw = iv.half_width(pt)
                rows.append({"split": split, "seed": seed, "method": mode, **{f"{k}_by_pred": v for k, v in ac.coverage_report(y[te], pt, hw, np.digitize(pt, np.quantile(pc, [1 / 3, 2 / 3]))).items()},
                             **{f"{k}_by_true": v for k, v in ac.coverage_report(y[te], pt, hw, act).items() if k in ("coverage", "worst_group")},
                             "rmse": float(np.sqrt(np.mean((y[te] - pt) ** 2)))})
    return pd.DataFrame(rows)


def summarise(df):
    out = []
    for (split, method), g in df.groupby(["split", "method"]):
        r = {"split": split, "method": method}
        for c in ("coverage_by_pred", "worst_group_by_pred", "worst_group_by_true", "width_by_pred", "rmse"):
            m, h = ac.mean_ci(g[c]); r[c] = round(m, 3); r[c + "_ci95"] = round(h, 3)
        out.append(r)
    return pd.DataFrame(out)
