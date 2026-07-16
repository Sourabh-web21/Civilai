# CivilAI Desktop Verification

## Windows Check

From the repository root:

```powershell
$env:DEBUG='False'
npm.cmd run build --prefix frontend
.\venv\Scripts\python.exe -m PyInstaller packaging\pyinstaller\civilai-backend.spec --noconfirm
powershell -ExecutionPolicy Bypass -File packaging\prepare_tauri_sidecar.ps1 -TargetTriple x86_64-pc-windows-msvc
cmd /c "call C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat && set PATH=%USERPROFILE%\.cargo\bin;%PATH% && cd desktop\src-tauri && cargo tauri build"
```

Expected artifact:

```text
desktop/src-tauri/target/release/bundle/msi/CivilAI_0.1.0_x64_en-US.msi
```

Smoke check:

```powershell
.\desktop\src-tauri\target\release\CivilAI.exe
```

Then open AiConnect. The Local Meeting Recorder backend pill should show the
Windows WASAPI backend and should be ready on machines with normal output audio.

## macOS Build

Run this on the Mac client machine or on a GitHub Actions macOS runner:

```bash
chmod +x packaging/macos/build_macos.sh packaging/macos/smoke_test_macos.sh
packaging/macos/build_macos.sh
packaging/macos/smoke_test_macos.sh
```

Expected artifacts are under:

```text
desktop/src-tauri/target/release/bundle/
```

Typical files:

```text
desktop/src-tauri/target/release/bundle/macos/CivilAI.app
desktop/src-tauri/target/release/bundle/dmg/*.dmg
```

## macOS Audio Check

macOS does not expose system output audio as an input by default.

1. Install BlackHole 2ch.
2. Open Audio MIDI Setup.
3. Create a Multi-Output Device with your speakers/headphones and BlackHole 2ch.
4. Select that Multi-Output Device as system output.
5. Open CivilAI.
6. Go to AiConnect.
7. Confirm Local Meeting Recorder shows `macos-virtual-loopback` and ready.
8. Download `Whisper tiny.en` in Offline Models.
9. Start a meeting, play audio from the Mac, wait for transcript segments, stop,
   and export Markdown/PDF.

## What Passing Looks Like

- App opens without terminal.
- Backend starts automatically on a dynamic localhost port.
- AiConnect loads.
- Offline Models list appears.
- Whisper model download reaches 100%.
- Local Meeting Recorder reports audio backend ready.
- Start Meeting changes status to recording and timer increments.
- Transcript segments appear after audio is played.
- Stop & build MOM creates a summary.
- Exports create Markdown/TXT/DOCX/PDF files.
