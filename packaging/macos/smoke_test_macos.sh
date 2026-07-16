#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="${1:-$ROOT/desktop/src-tauri/target/release/bundle/macos/CivilAI.app}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must run on macOS." >&2
  exit 1
fi

if [[ ! -d "$APP" ]]; then
  echo "App bundle not found: $APP" >&2
  exit 1
fi

open "$APP"

echo "Waiting for bundled backend..."
for _ in {1..90}; do
  PORTS="$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | awk '/civilai-backend/ { split($9,a,\":\"); print a[length(a)] }' | sort -u || true)"
  for PORT in $PORTS; do
    if curl -fsS "http://127.0.0.1:${PORT}/api/v1/project/local-meeting/backend-status" >/tmp/civilai-backend-status.json; then
      echo "Backend port: ${PORT}"
      cat /tmp/civilai-backend-status.json
      echo
      osascript -e 'tell application "CivilAI" to quit' >/dev/null 2>&1 || true
      exit 0
    fi
  done
  sleep 1
done

osascript -e 'tell application "CivilAI" to quit' >/dev/null 2>&1 || true
echo "Backend did not become ready." >&2
exit 1
