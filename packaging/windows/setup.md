# CivilAI Windows Setup

## Install

Install `desktop/src-tauri/target/release/bundle/msi/CivilAI_0.1.0_x64_en-US.msi`.
The MSI includes the Tauri frontend and packaged Python backend. Users do not
need Python, Node.js, Rust, Ollama, or CUDA.

Default local login:

- Email: `admin@civil.ai`
- Password: `admin12345`

For local meeting capture, Windows audio loopback must be available. AiConnect
shows the detected WASAPI loopback status.

## Build

Run from the repository root in PowerShell:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\venv\Scripts\python.exe -m PyInstaller packaging\pyinstaller\civilai-backend.spec --noconfirm
powershell -ExecutionPolicy Bypass -File .\packaging\prepare_tauri_sidecar.ps1
cmd /c "call C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat && set PATH=%USERPROFILE%\.cargo\bin;%PATH% && cargo tauri build"
```

Share only the generated MSI. Do not share `.env`, `venv`, `target`, databases,
logs, or cached email attachments.
