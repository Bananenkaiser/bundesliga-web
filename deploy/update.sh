#!/usr/bin/env bash
# Auf dem Raspberry Pi ausführen: holt den neuesten Stand und baut den Container neu.
# Aufruf:  ~/projects/bundesliga-web/deploy/update.sh
set -euo pipefail

cd "$(dirname "$0")/.."

git pull --ff-only
docker compose up -d --build
docker image prune -f

echo "fertig – http://tippspiel.lan"
