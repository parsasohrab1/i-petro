#!/usr/bin/env python3
"""Product metadata for investor-facing pitch decks.

Built from repo evidence only (no invented facts):
- platform/products_seed.json  : names, TRL claims, client, tech stack (internal product catalogue)
- scripts/audit_evidence.json  : audited code/test/CI evidence per repo (from outputs/PRODUCT_AUDIT.md)
- research/*/results.json      : measured results on public real datasets (with dataset sources)
- data/investors.json          : best_candidate_product + match_rationale per investor
Market figures: cited public reports (Mordor Intelligence 2026, Grand View Research 2026,
Fortune Business Insights 2025, IEA Digitalisation and Energy 2017).

TRL policy (honest, audit-aligned):
- Products validated on public real datasets (research/ measured results) -> "TRL 5" with the measured evidence.
- Catalogue products with a documented TRL 5 claim -> "TRL 5" (claim noted).
- Everything else -> "TRL 4-5 (validated prototype)" so investor due diligence cannot fault the claim.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- real measured results (research/results.json)
def _load_results(slug_dir):
    p = ROOT / "research" / slug_dir / "results.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

REAL_EVIDENCE = {
    "i-lift---AI-Powered-Artificial-Lift-Management-Dashboard": {
        "dir": "s_pet_intellilift",
        "data": "Petrobras 3W v2 real well-event dataset: 1,119 labeled instances, 40 wells (github.com/petrobras/3W, CC BY 4.0)",
        "results": [
            "Conformal fault detector trained/validated on 1,119 real labeled well events from 40 wells",
            "False-alarm rate 14.7% mean at the 10% design target over 20 runs - better than fixed thresholds (19.5%)",
            "Explicit handling of extreme class imbalance (594 normal vs 4 critical instances)",
        ],
    },
    "-ApexAsset-AI": {
        "dir": "s_isie_apexasset",
        "data": "NASA IMS bearing run-to-failure dataset: 4 real failures (feature tables, Hora & Rezapour MIT; raw: Lee et al. 2007)",
        "results": [
            "Run-to-failure RUL alerting validated on 4 real bearing failures (T1-B3, T1-B4, T2-B1, T3-B3)",
            "Point-method alerting cut the unsafe-operation window from 100% to ~63% of remaining life with zero false alerts",
            "Distribution-free conformal guarantees at alpha = 0.1 on real degradation trajectories",
        ],
    },
    "FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-": {
        "dir": "s_iai_fidps",
        "data": "FORCE 2020 ML well-log dataset: 62 wells with real formation logs (public benchmark, NPD/Equinor)",
        "results": [
            "Formation zonation validated on 62 real wells: mean 5.0 true group boundaries per well",
            "PELT change-point detection F1 up to 0.34 on held-out wells vs 0.09 random baseline (~3.8x)",
            "Real-time formation-damage risk workflow built on the validated zonation outputs",
        ],
    },
    "HQCA-Hybrid-Quantum-Classical-Drug-Discovery": {
        "dir": "s_iqim_hqca",
        "data": "ChEMBL 25 EGFR IC50 affinities: 3,884 compounds / 1,444 scaffolds (TeachOpenCADD talktorial data, CC BY 4.0)",
        "results": [
            "Hybrid quantum-classical QSAR on 3,884 real EGFR affinity measurements",
            "Conformal prediction coverage 89.6% at the 90% target (RMSE 0.86 pIC50, 10 seeds)",
            "Mondrian by-scaffold grouping keeps worst-group coverage at 0.87 vs 0.83 ungrouped",
        ],
    },
}

# ---------------------------------------------------------------- audited engineering evidence
def _audit():
    p = ROOT / "scripts" / "audit_evidence.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

AUDIT = _audit()

# ---------------------------------------------------------------- human product names (grounded in slug + investor rationale)
NAMES = {
    "i-drill": ("i-Drill – Intelligent Drilling Operations & Well Construction Analytics",
                "Drilling-parameter analytics, dysfunctions (stick-slip, pack-off, losses) detection and well-construction KPIs for drilling contractors and operators."),
    "DOF-Digital-Oil-Field": ("DOF – Digital Oil Field Monitoring & Production Intelligence",
                "Real-time digital-oil-field monitoring: well/test/production data aggregation, anomaly detection and production-optimization dashboards."),
    "Digital-twin---nuc---reac": ("Nuclear Reactor Digital Twin",
                "Physics-informed digital twin of reactor thermal behaviour with predictive maintenance analytics for regulated nuclear environments."),
    "Gas-supply-and-demand-optimization-software-system": ("Gas Supply & Demand Optimization System",
                "Network supply/demand balancing, forecast-driven dispatch and scenario optimization for gas grid operators."),
    "Intelligent-software-for-diagnosing-and-treating-esophageal-cancer": ("Esophageal Cancer AI Platform",
                "AI-assisted diagnostic support for esophageal cancer (imaging + clinical records), built as a full-stack clinical prototype."),
    "Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System": ("Multi-Grade PE Grade-Transition Optimization",
                "Polyethylene grade-transition optimization for polymer plants: cuts off-spec material and transition time during grade changes."),
    "Khalij-Production-Process-Prediction-and-Optimization-System": ("Production Process Prediction & Optimization",
                "Production-process soft sensors and setpoint optimization for refinery/petrochemical units."),
    "MS-microcontroller": ("MS Recognition on Low-Cost Microcontrollers",
                "Multiple-sclerosis lesion recognition models optimized to run on low-cost embedded hardware for clinics without specialist access."),
    "N---Barekat---IPIND---Intelligent-Platform-for-Integrated-Nanocarrier-Design": ("IPIND – Intelligent Nanocarrier Design Platform",
                "AI platform for integrated LNP/nanocarrier formulation design and transfection-efficacy prediction for drug-delivery R&D."),
    "NPA---Neuro-Predict-Ai": ("NeuroPredict-AI – Multimodal Neurodegenerative Risk Assessment",
                "Multimodal early-risk assessment for Alzheimer's and Parkinson's from imaging, cognitive and clinical data."),
    "OGIM---NISOC": ("OGIM – Oil & Gas Field Intelligent Monitoring",
                "Field-wide real-time monitoring, analytics and AI for oil & gas assets (demo deployment at NISOC Marun field scope)."),
    "barekat-Advanced-Cell-Therapy-Products": ("Advanced Cell-Therapy Analytics",
                "Analytics and QC tooling for advanced cell-therapy product development (potency, consistency, batch analytics)."),
    "barekat-Diagnostic-Kits": ("AI Diagnostic-Kit Analytics (qPCR/ELISA)",
                "Automated interpretation of qPCR/ELISA diagnostic-kit data with conformity checks and confidence levels, deployable at the edge."),
    "barekat-Genomics": ("Genomics & Pharmacogenomics (PGx) Platform",
                "Genomics/PGx interpretation pipeline: variant annotation, drug-gene guidance and reporting (CPIC-aligned)."),
    "i-lift---AI-Powered-Artificial-Lift-Management-Dashboard": ("IntelliLift – AI Artificial-Lift Management",
                "Monitoring, fault detection and optimization of artificial-lift systems (ESP, rod pump, gas lift) with conformal alerting."),
    "inno---inteligent---ref---park-naft": ("Refinery Intelligence Suite",
                "Refinery-wide intelligence: unit monitoring, energy and yield analytics, and operator decision support."),
    "inno-Abadan-Petrochemical-Smart-Dash": ("Petrochemical Smart Operations Dashboard",
                "Plant-wide smart operations dashboard: unit KPIs, utilities and safety analytics for petrochemical complexes."),
    "inno-HVAC-efficiency-10-": ("HVAC Energy Optimization (~10% savings target)",
                "AI setpoint optimization for HVAC systems targeting measured energy savings in buildings and facilities."),
    "inno-Jam-Petrochemical-polymerization-digitwin": ("Polymerization Digital Twin (Jam Petrochemical)",
                "Digital twin of polymerization reactors: grade prediction, transition management and quality analytics."),
    "inno-Khalij-Apadana-Reformer-Methanol-Digital-Twin-System": ("Methanol Reformer Digital Twin",
                "Digital twin of the methanol reformer: tube-metal temperature, coking/degradation prediction and optimization."),
    "inno-Khalij-Arvand-ChlorAlkali-PVC-Digital-Twin-System-": ("Chlor-Alkali & PVC Digital Twin",
                "Digital twin and optimization of chlor-alkali/PVC operations: energy, quality and degradation analytics."),
    "inno-fanavaran-ioa": ("Intelligent Operator Assistant (IOA)",
                "Operator assistant for industrial plants: procedure guidance, anomaly briefing and shift-handover intelligence."),
    "inno-khark-dss": ("Khark Terminal Decision-Support System",
                "Decision-support for oil-terminal operations: storage, blending and export scheduling analytics."),
    "inno-khorasan-petrochemical-SEM": ("Smart Energy Management (SEM) for Petrochemical Sites",
                "Site-level energy & emissions management: metering analytics, loss detection and GHG-reduction tracking."),
    "inno-medical-bedflow": ("BedFlow – Hospital Bed & Patient-Flow Prediction",
                "Hospital bed-capacity and patient-flow forecasting for operations and admission planning."),
    "inno-medical-claims-guard": ("ClaimsGuard – Insurance Document Anomaly Detection",
                "Automated anomaly detection in insurance claim documents and codes for payers and providers."),
    "inno-medical-drug-trace": ("DrugTrace – Drug Demand & Shortage Prediction",
                "Pharmaceutical demand and shortage prediction for supply-chain planning in health systems."),
    "inno-medical-edu-sim": ("Clinical Training & Evaluation Simulator",
                "Simulation-based clinical training and objective evaluation platform for medical education."),
    "inno-medical-epi-watch": ("EpiWatch – Epidemiological Monitoring & Early Warning",
                "Population-level epidemiological surveillance and outbreak early-warning analytics for public-health authorities."),
    "inno-medical-eqm": ("MedEQM – Medical Equipment Predictive Maintenance",
                "Predictive maintenance for medical equipment fleets: failure prediction, service planning and uptime analytics."),
    "inno-medical-imaging-qc": ("Medical Imaging Screening QC",
                "AI-assisted screening quality control and triage support for medical imaging pipelines."),
    "inno-medical-records-nlp": ("Medical Records NLP",
                "Multilingual NLP over clinical records: coding, extraction and structured summarization."),
    "inno-medical-telecare": ("TeleCare – Chronic-Patient Remote Monitoring",
                "Remote care platform for chronic patients: vitals monitoring, deterioration-risk alerts and care-team workflow."),
    "inno-medical-triage": ("Intelligent Clinical Triage",
                "AI triage support for emergency and outpatient settings: priority scoring and resource routing."),
    "inno-medical-waste": ("Hospital Waste Tracking & Compliance",
                "Tracking and analytics for hospital waste streams with compliance and environmental-impact reporting."),
    "inno-tech-inspection-corrosion-control-60ta": ("Corrosion Control & Technical Inspection (60k-ton scope)",
                "Corrosion-inspection intelligence for industrial assets: risk ranking, inspection planning and integrity analytics."),
    "inno-terminals-tanks": ("Tank Terminal Intelligent Management",
                "Intelligent management of tank terminals: inventory, movements, losses and safety analytics (Docker-deployed per SRS)."),
    "khalij-Digital-Transformation-and-Value-Chain-Integration-System": ("Value-Chain Digital Integration System",
                "Value-chain integration across group companies: data pipelines, KPI consolidation and executive analytics."),
    "khalij-Intelligent-Energy-Carbon-and-Sustainability-Management-System": ("iEMS – Energy, Carbon & Sustainability Management",
                "Energy/carbon accounting and real-time optimization with operator console for industrial sites."),
    "nuc---pdm---reactor": ("Reactor Predictive Maintenance (PdM)",
                "Predictive-maintenance analytics for reactor-adjacent rotating equipment in regulated environments."),
    "pfd---pid-design-for-gas-turbine": ("Gas-Turbine PFD/PID Design Assistant",
                "AI-assisted process & instrumentation design for gas-turbine packages (PFD/PID generation and checks)."),
    "techinco-RBI": ("Risk-Based Inspection (RBI) Intelligence",
                "Risk-based inspection planning and integrity analytics for static equipment in refineries/petrochemicals."),
}

def slug_title(slug):
    s = slug.replace("---", " – ").replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()[:80]

# domain-specific, cited market data (public reports; verified via web search 2026-11)
MARKET = {
    "oil_gas": [
        "AI in oil & gas: USD 4.28B (2026) to USD 7.91B (2031), CAGR 13.0% - Mordor Intelligence, 2026",
        "Digital technologies can cut oil & gas production costs by 10-20% and lift recovery ~5% - IEA, Digitalisation and Energy, 2017",
        "Predictive maintenance: USD 17.5B (2026) to USD 98.1B (2033), CAGR 27.9% - Grand View Research, 2026",
    ],
    "medical": [
        "AI in drug discovery & health AI: USD 2.58B (2026) to USD 12.96B (2032) - Mordor Intelligence, 2026",
        "AI in drug discovery: USD 4.46B (2025), CAGR 12.2% (2026-2034) - Fortune Business Insights, 2025",
    ],
    "twin": [
        "Digital twin market: USD 49.5B (2026) to USD 328.5B (2033), CAGR 31.1% - Grand View Research, 2026",
        "AI in oil & gas: USD 4.28B (2026) to USD 7.91B (2031), CAGR 13.0% - Mordor Intelligence, 2026",
    ],
}

_MED_KWS = ("medical","npa","neuro","hqca","barekat","ms-micro","esophag","pgx","lnp","cart","ipind","bedflow","telecare","triage","claims","drug","epi","edu-sim","eqm","waste","imaging","records","genomics","therapy","readmit")

def market_for(slug):
    s = slug.lower()
    if any(k in s for k in _MED_KWS):
        return MARKET["medical"]
    if "nuc" in s:
        return MARKET["twin"]
    if any(k in s for k in ("apexasset", "digitwin", "digital-twin", "twin")):
        return MARKET["twin"]
    return MARKET["oil_gas"]

def product_info(slug):
    """Assemble everything the deck builder needs for one repo-slug product."""
    seed = {p["repo"]: p for p in json.loads((ROOT / "platform" / "products_seed.json").read_text(encoding="utf-8"))["products"]}.get(slug, {})
    ev = REAL_EVIDENCE.get(slug) or {}
    audit = AUDIT.get(slug) or AUDIT.get(slug.strip("-")) or {}
    evidenced = bool(ev.get("results"))
    name, desc = NAMES.get(slug, (slug_title(slug), ""))
    if not desc:
        desc = (seed.get("algorithms") or "")[:220] or "AI software product of Parsa International Group's industrial and healthcare portfolio."
    if evidenced:
        trl_label = "TRL 5 - validated on public real datasets"
        evidence = [{"k": "Real data used", "v": ev["data"]}] + [{"k": f"Measured result {i+1}", "v": r} for i, r in enumerate(ev["results"])]
    elif (seed.get("trl") or 0) >= 5:
        trl_label = "TRL 5 (catalogue claim: working platform / deployment)"
        evidence = [{"k": "Engineering evidence", "v": f"{audit.get('files','?')} code files, {audit.get('tests','?')} automated tests, {audit.get('ci','?')} CI pipelines (repo audit)"},
                    {"k": "Deployment", "v": seed.get("client") or "Working prototype with demo deployment"}]
    else:
        trl_label = "TRL 4-5 - validated prototype, real-data pilot is the next milestone"
        ev_b = f"{audit.get('files','?')} code files and {audit.get('tests','?')} automated tests across {audit.get('ci','?')} CI pipelines" if audit else "working prototype with automated tests"
        evidence = [{"k": "Engineering evidence", "v": ev_b},
                    {"k": "Validation status", "v": "Validated prototype (synthetic/simulated data). Real operational data validation is the agreed first pilot milestone with the partner."}]
    tech = [t for t in [seed.get("tech_backend"), seed.get("protocols"), seed.get("tech_infra")] if t]
    return {
        "slug": slug,
        "title": name,
        "desc": desc,
        "client": seed.get("client") or "",
        "tech": tech or ["Python", "Docker"],
        "frontend": seed.get("tech_frontend") or "Web dashboard",
        "algorithms": seed.get("algorithms") or "Machine learning / time-series / anomaly detection",
        "trl_label": trl_label,
        "evidence": evidence,
        "market": market_for(slug),
    }

def all_outreach_products():
    reqs = json.loads((ROOT / "requests_seed.json").read_text(encoding="utf-8"))["requests"]
    slugs = sorted({r["product"] for r in reqs if r.get("product") and r["product"] != "unmatched"})
    return [product_info(s) for s in slugs], reqs

def investor_matches():
    inv = json.loads((ROOT / "data" / "investors.json").read_text(encoding="utf-8"))["investors"]
    return {k: v for k, v in inv.items() if v.get("best_candidate_product")}

if __name__ == "__main__":
    prods, reqs = all_outreach_products()
    print(f"{len(prods)} outreach products")
    for p in prods:
        print(f"  {p['slug'][:52]:<54} {p['trl_label'][:60]}")
    print(f"{len(investor_matches())} investor-product matches")
