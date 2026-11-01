#!/usr/bin/env bash
# Creates one private GitHub repository per petrochemical plant from this product (needs: gh, git, permission to create repos).
# Usage: tools/split_repos.sh <github-owner>
set -euo pipefail
OWNER="${1:?usage: split_repos.sh <github-owner>}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
for f in "$HERE"/plants/*.json; do
  slug="$(basename "$f" .json)"
  repo="petro-energy-${slug//_/-}"
  tmp="$(mktemp -d)"
  cp -r "$HERE/petro_energy" "$HERE/README.md" "$tmp/"
  mkdir "$tmp/plants" && cp "$f" "$tmp/plants/"
  mkdir -p "$tmp/reports" && (cd "$tmp" && python3 -m petro_energy build --plant "$slug" --out reports >/dev/null)
  (cd "$tmp" && git init -q -b main && git add -A && git commit -q -m "PetroEnergy for ${slug} (TRL 4, synthetic data)")
  gh repo create "$OWNER/$repo" --private --source "$tmp" --push --description "PetroEnergy: fuel and energy optimisation for ${slug} (TRL 4, synthetic data)"
  echo "created $OWNER/$repo"
done
