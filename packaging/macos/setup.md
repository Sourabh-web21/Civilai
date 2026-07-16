# CivilAI macOS Setup

## Install

Open the generated DMG and drag CivilAI to Applications. Use the Apple Silicon
DMG for M-series Macs and the Intel DMG for Intel Macs.

For local system-audio meetings, install BlackHole 2ch, create a Multi-Output
Device in Audio MIDI Setup containing the real output and BlackHole, select it
as the sound output, and grant CivilAI microphone and screen/audio permissions.

## Build

Build on macOS:

```bash
chmod +x packaging/macos/build_macos.sh
./packaging/macos/build_macos.sh
```

Artifacts are under `desktop/src-tauri/target/release/bundle/`. Build once on
Apple Silicon and once on Intel, or use separate macOS CI runners.

## Share

Share only the architecture-matching `.dmg`. Do not share `.env`, `venv`,
databases, logs, or model caches. Users download models from AiConnect.
