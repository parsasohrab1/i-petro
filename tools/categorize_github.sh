#!/usr/bin/env bash
# Tags every product repo with GitHub topics so the account can be filtered by domain:
#   domain-medical, domain-oil-gas, domain-nuclear, domain-aerospace  (+ domain-other for urban/energy-management items)
# Usage: gh auth login (once), then: bash tools/categorize_github.sh
set -u
OWNER=parsasohrab1
tag(){ cat | while read -r repo; do [ -z "$repo" ] && continue; echo "$repo <- $*"; args=(); for t in "$@"; do args+=(--add-topic "$t"); done; gh repo edit "$OWNER/$repo" "${args[@]}" || echo "  FAILED $repo"; done; }

tag domain-medical <<'L'
barekat-Advanced-Cell-Therapy-Products
barekat-Diagnostic-Kits
BAREKAT-Big-Data-Analytics-in-Health
HQCA-Hybrid-Quantum-Classical-Drug-Discovery
Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
N---Barekat---IPIND---Intelligent-Platform-for-Integrated-Nanocarrier-Design
barekat-gen-therapy
NPA---Neuro-Predict-Ai
barekat-Genomics
L
tag domain-oil-gas <<'L'
inno---inteligent---ref---park-naft
FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-
Gas-supply-and-demand-optimization-software-system
khalij-Intelligent-Energy-Carbon-and-Sustainability-Management-System
i-lift---AI-Powered-Artificial-Lift-Management-Dashboard
OGIM---NISOC
inno-Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System-
inno-terminals-tanks
L
tag domain-oil-gas domain-aerospace <<'L'
-ApexAsset-AI
digital-twine-gas-turbine
L
tag domain-nuclear <<'L'
Digital-twin---nuc---reac
L
tag domain-other <<'L'
khalij-Digital-Transformation-and-Value-Chain-Integration-System
inno-HVAC-efficiency-10-
L
echo "Done. On GitHub: open your profile > Repositories > filter by topic, e.g. https://github.com/$OWNER?tab=repositories&q=topic%3Adomain-medical"
