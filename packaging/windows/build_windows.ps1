$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-local-ai.txt pyinstaller
python -m PyInstaller packaging\pyinstaller\civilai-backend.spec --noconfirm
powershell -ExecutionPolicy Bypass -File .\packaging\prepare_tauri_sidecar.ps1

if (-not (Get-Command cargo-tauri -ErrorAction SilentlyContinue)) {
    cargo install tauri-cli --version '^1.6' --locked
}
cargo tauri build
Write-Host "Windows installers are in desktop/src-tauri/target/release/bundle"
