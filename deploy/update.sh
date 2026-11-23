#!/usr/bin/env bash
# Update a running iPetro server to the latest code in GitHub (run on the VPS, from any folder).
#   bash /opt/ipetro/deploy/update.sh            # pull main and rebuild
#   bash /opt/ipetro/deploy/update.sh some-branch
# If the VPS cannot reach GitHub, push the code with rsync instead (see deploy/README.md, step 2) and run only the last two lines.
set -euo pipefail
cd "$(dirname "$0")/.."
BRANCH="${1:-main}"
if [ -d .git ]; then
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi
cd deploy
docker compose up -d --build
docker compose ps
curl -ksf https://localhost/healthz && echo " healthz ok"
