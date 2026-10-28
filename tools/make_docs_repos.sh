#!/usr/bin/env bash
# Creates one private "<repo>-docs" repo per product containing ONLY the SRS, the product architecture and the outputs.
# Code never leaves the source repo. Members are then invited to the -docs repo with the Read role.
# Usage: gh auth login   (once)   then   bash tools/make_docs_repos.sh OWNER repos.txt [member1,member2,...]
#   repos.txt: one source repo name per line (private repos of OWNER)
set -euo pipefail
OWNER="$1"; LIST="$2"; MEMBERS="${3:-}"
# Which paths count as "documentation" (everything else, i.e. code, is left out)
KEEP='(^|/)(SRS[^/]*|srs[^/]*|README[^/]*|docs|doc|architecture|outputs?|results?|reports?|figures?|diagrams?)(/|\.[a-z]+$|$)'
WORK="$(mktemp -d)"
while read -r SRC; do
  [ -z "$SRC" ] && continue
  DOCS="${SRC}-docs"; DIR="$WORK/$SRC"
  git clone -q "https://github.com/$OWNER/$SRC.git" "$DIR/src" || { echo "skip $SRC (clone failed)"; continue; }
  mkdir -p "$DIR/docs"
  (cd "$DIR/src" && git ls-files | grep -Ei "$KEEP" | grep -Evi '\.(py|js|ts|tsx|jsx|java|go|rs|c|cpp|h|ipynb|sh|env|pem|key)$' || true) | while read -r f; do
    mkdir -p "$DIR/docs/$(dirname "$f")"; cp "$DIR/src/$f" "$DIR/docs/$f"
  done
  [ -z "$(ls -A "$DIR/docs")" ] && { echo "skip $SRC (no SRS/architecture/outputs found)"; continue; }
  gh repo view "$OWNER/$DOCS" >/dev/null 2>&1 || gh repo create "$OWNER/$DOCS" --private --description "Documentation only (SRS, architecture, outputs) for $SRC"
  ( cd "$DIR/docs" && git init -q -b main && git add -A && git commit -q -m "Docs snapshot of $SRC" && git remote add origin "https://github.com/$OWNER/$DOCS.git" && git push -q -f origin main )
  for m in ${MEMBERS//,/ }; do gh api -X PUT "repos/$OWNER/$DOCS/collaborators/$m" -f permission=pull >/dev/null && echo "  invited $m (read) to $DOCS"; done
  echo "ok $DOCS"
done < "$LIST"
echo "Review each -docs repo before inviting anyone: check that no secret or sensitive file was copied."
