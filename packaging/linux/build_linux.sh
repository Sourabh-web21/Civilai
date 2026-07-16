#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) TARGET_TRIPLE="x86_64-unknown-linux-gnu" ;;
  aarch64|arm64) TARGET_TRIPLE="aarch64-unknown-linux-gnu" ;;
  *) echo "Unsupported Linux architecture: $ARCH" >&2; exit 1 ;;
esac
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-local-ai.txt pyinstaller
python -m PyInstaller packaging/pyinstaller/civilai-backend.spec --noconfirm
mkdir -p dist/sidecars
cp dist/civilai-backend "dist/sidecars/civilai-backend-${TARGET_TRIPLE}"
chmod +x "dist/sidecars/civilai-backend-${TARGET_TRIPLE}"
cd frontend
npm ci
npm run build
cd "$ROOT/desktop/src-tauri"
if ! command -v cargo-tauri >/dev/null 2>&1 && ! cargo tauri --version >/dev/null 2>&1; then
  cargo install tauri-cli --version '^1.6' --locked
fi
cargo tauri build
echo "Linux bundles are in $ROOT/desktop/src-tauri/target/release/bundle"
