# Real-data catalogue for the 20 article abstracts (private)

Status as of this branch. "Reachable" = downloadable from this environment (GitHub / PyPI only). Licences must be verified before publication.

| Venue | Product | Real data | Source | Status |
|---|---|---|---|---|
| s_isie | ApexAsset AI | NASA IMS bearings (4 failures) | GitHub-hosted IMS features | **done** – research/s_isie_apexasset |
| s_iqim | HQCA | ChEMBL EGFR affinities (3,884) | TeachOpenCADD GitHub CSV | **done** – research/s_iqim_hqca |
| s_eg | StratGuard | SEG 2016 (10 wells), FORCE 2020 (81 wells) | GitHub mirrors | **done** – research/s_eg_stratguard (verify FORCE licence) |
| s_pet | IntelliLift | Petrobras 3W v2, 1,119 real instances | github.com/petrobras/3W (CC BY 4.0) | **done** – research/s_pet_intellilift |
| s_iqicsa | QGrid-Part | IEEE case9/case14 + AC power flow | PyPI pandapower | **done** – research/s_iqicsa_qgrid |
| s_icqe | StretchWatch | computed Hamiltonians, FCI/CCSD(T) | PyPI pyscf | **done** – research/s_icqe_stretchwatch |
| s_qip | Shot-Budget Lab | computed Hamiltonians (no hardware data exist publicly) | PyPI pyscf, openfermion | **done** – research/s_qip_shotlab |
| s_iai | FIDPS | FORCE 2020 group boundaries (surrogate; no damage data) | GitHub mirror | **done** – research/s_iai_fidps |
| s_npj | WearShift | UCI HAR (30 subjects) | archive.ics.uci.edu | blocked – needs the zip from the owner (GitHub repos found hold only download scripts) |
| s_mie | ReadmitCal | UCI Diabetes 130-US hospitals | archive.ics.uci.edu | blocked – Pima diabetes (reachable) is NOT a readmission data set and is not used |
| s_mimar | Gas turbine twin | UCI Gas Turbine CO/NOx | archive.ics.uci.edu | blocked |
| s_jpse | Smart terminals & tanks | EIA weekly crude stocks | eia.gov | blocked (oil-price CSVs on GitHub are prices, not inventories) |
| s_hydro | HydroGate | CAMELS / USGS streamflow | NCAR, USGS | blocked |
| s_quantics | QRNG-Audit | IBM QRNG bits, ANU QRNG, NIST STS | Zenodo, qrng.anu.edu.au | blocked |
| s_cmi | ExplainGuard | PneumoniaMNIST / chest X-ray | Zenodo (MedMNIST), NIH | blocked |
| s_jimg | Genomics & PGx | CPIC, gnomAD, 1000 Genomes | cpicpgx.org, gnomad | blocked |
| s_icmhi, s_aimh | IPIND, LNP | LNP transfection (LANTERN) | repository not found among reachable GitHub repos | blocked |
| s_front_nuc | Nuclear twin | accident simulator data | no public source found | none |
| s_ps | Petrochemical twin | polyethylene melt-index plant data | no public source found | none |

To unblock: open Network access for the hosts above (Settings > environment > Network), or put the files in a private repo folder `research-data/` / Google Drive and share the link. Then run the module for the venue and rewrite the abstract only with measured numbers.
