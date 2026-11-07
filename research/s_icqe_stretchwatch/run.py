"""python -m research.s_icqe_stretchwatch.run -> results.json"""
import json
import numpy as np
from scipy.stats import spearmanr
from . import stretch

SCANS = {"H2": [0.5, 0.74, 1.0, 1.5, 2.0, 3.0, 4.0], "LiH": [1.0, 1.6, 2.0, 3.0, 4.0, 6.0, 8.0],
         "BeH2": [1.0, 1.33, 1.8, 2.5, 3.5, 5.0], "H2O": [0.8, 0.96, 1.3, 1.7, 2.2, 3.0]}


if __name__ == "__main__":
    pts = [stretch.point(m, r) for m, rs in SCANS.items() for r in rs]
    pts += [stretch.point("LiH", r, "6-31g") for r in SCANS["LiH"]]
    for p in pts:
        p["err_hf_mHa"] = 1e3 * (p["e_hf"] - p["e_fci"])
        if p["e_ccsd"] is not None:
            p["err_ccsd_mHa"] = 1e3 * (p["e_ccsd"] - p["e_fci"]); p["err_ccsd_t_mHa"] = 1e3 * (p["e_ccsd_t"] - p["e_fci"])
    for p in pts:
        p["scf_suspect"] = p["e_ccsd"] is None or abs(p["err_ccsd_mHa"]) > 50     # RHF/CCSD landed on a wrong (ionic) solution, not a property of the molecule
    rho = {}
    for m in SCANS:
        q = [p for p in pts if p["mol"] == m and p["basis"] == "sto-3g" and not p["scf_suspect"]]
        rho[m] = dict(spearman_overlap_vs_entropy=float(spearmanr([p["overlap2"] for p in q], [p["entropy"] for p in q])[0]),
                      spearman_overlap_vs_hf_error=float(spearmanr([p["overlap2"] for p in q], [p["err_hf_mHa"] for p in q])[0]))
    json.dump(dict(points=pts, rank_correlations=rho), open("research/s_icqe_stretchwatch/results.json", "w"), indent=1)
    for p in pts:
        print("SUSPECT" if p["scf_suspect"] else "", p["mol"], p["basis"], p["r"], f'ov2={p["overlap2"]:.3f} S={p["entropy"]:.2f} HF-FCI={p["err_hf_mHa"]:.1f} CCSD={p.get("err_ccsd_mHa", float("nan")):.2f} CCSD(T)={p.get("err_ccsd_t_mHa", float("nan")):.2f}')
    print(rho)
