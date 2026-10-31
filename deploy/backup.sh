#!/usr/bin/env bash
# Daily PostgreSQL backup. Cron:  15 2 * * *  /opt/ipetro/deploy/backup.sh
# Keeps 14 days locally; set REMOTE (user@host:/path) to copy each dump to a second machine as well.
set -euo pipefail
cd "$(dirname "$0")"
DIR="${BACKUP_DIR:-/var/backups/ipetro}"
mkdir -p "$DIR"
FILE="$DIR/ipetro-$(date +%F-%H%M).sql.gz"
docker compose exec -T db pg_dump -U ipetro ipetro | gzip > "$FILE"
[ -s "$FILE" ] || { echo "empty backup" >&2; rm -f "$FILE"; exit 1; }
find "$DIR" -name 'ipetro-*.sql.gz' -mtime +14 -delete
if [ -n "${REMOTE:-}" ]; then rsync -a "$FILE" "$REMOTE"; fi
echo "ok $FILE"
