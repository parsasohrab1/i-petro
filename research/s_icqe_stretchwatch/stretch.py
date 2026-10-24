"""HF reference quality along bond-stretching curves, with FCI / CCSD / CCSD(T) from PySCF (computed, not measured, Hamiltonians)."""
import numpy as np
from pyscf import gto, scf, fci, cc

ANG = {"H2": lambda r: f"H 0 0 0; H 0 0 {r}",
       "LiH": lambda r: f"Li 0 0 0; H 0 0 {r}",
       "BeH2": lambda r: f"Be 0 0 0; H 0 0 {r}; H 0 0 {-r}",
       "H2O": lambda r: f"O 0 0 0; H {r*np.sin(np.radians(52.25))} 0 {r*np.cos(np.radians(52.25))}; H {-r*np.sin(np.radians(52.25))} 0 {r*np.cos(np.radians(52.25))}"}


def entropy_from_occ(nocc):
    v = np.clip(np.asarray(nocc) / 2.0, 1e-12, 1 - 1e-12)
    return float(-np.sum(v * np.log(v) + (1 - v) * np.log(1 - v)))


def point(mol_name, r, basis="sto-3g"):
    mol = gto.M(atom=ANG[mol_name](r), basis=basis, verbose=0)
    mf = scf.RHF(mol); mf.conv_tol = 1e-10; mf.kernel()
    if not mf.converged:
        mf = scf.newton(mf); mf.kernel()
    ci = fci.FCI(mf); e_fci, vec = ci.kernel()
    nmo = mf.mo_coeff.shape[1]; ne = mol.nelec
    c0 = float(vec[0, 0])                                 # amplitude of the HF determinant (lowest orbitals occupied)
    dm1 = ci.make_rdm1(vec, nmo, ne)
    occ = np.sort(np.linalg.eigvalsh(dm1))[::-1]
    out = dict(mol=mol_name, basis=basis, r=r, e_hf=float(mf.e_tot), e_fci=float(e_fci), overlap2=c0 ** 2, entropy=entropy_from_occ(occ), converged=bool(mf.converged))
    try:
        m = cc.CCSD(mf).run(); out["e_ccsd"] = float(m.e_tot)
        out["e_ccsd_t"] = float(m.e_tot + m.ccsd_t())
    except Exception:
        out["e_ccsd"] = out["e_ccsd_t"] = None
    return out
