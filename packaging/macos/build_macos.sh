#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must run on macOS." >&2
  exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" == "arm64" ]]; then
  TARGET_TRIPLE="aarch64-apple-darwin"
else
  TARGET_TRIPLE="x86_64-apple-darwin"
fi

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip

export CMAKE_ARGS="${CMAKE_ARGS:--DGGML_METAL=on}"
python -m pip install -r requirements.txt -r requirements-local-ai.txt pyinstaller
python -m PyInstaller packaging/pyinstaller/civilai-backend.spec --noconfirm

mkdir -p dist/sidecars
cp "dist/civilai-backend" "dist/sidecars/civilai-backend-${TARGET_TRIPLE}"
chmod +x "dist/sidecars/civilai-backend-${TARGET_TRIPLE}"

cd frontend
npm ci
npm run build

cd "$ROOT/desktop/src-tauri"
if ! command -v cargo-tauri >/dev/null 2>&1 && ! cargo tauri --version >/dev/null 2>&1; then
  cargo install tauri-cli --version '^1.6' --locked
fi

cargo tauri build

echo "macOS bundles are in:"
echo "$ROOT/desktop/src-tauri/target/release/bundle"
