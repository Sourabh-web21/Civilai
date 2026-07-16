# CivilAI macOS Desktop Build Notes

CivilAI for macOS is built on a macOS runner because Apple app bundles and DMG
artifacts cannot be produced reliably from Windows.

## Build

The `Desktop Build` GitHub Actions workflow runs on `macos-latest` and produces:

- `CivilAI.app`
- `CivilAI_0.1.0_aarch64.dmg` or the Tauri-generated equivalent

## System Audio

The app records local system audio through the bundled Python `soundcard`
adapter. macOS does not expose system output as an input device by default, so
the first Mac client needs a loopback input available on the machine.

Recommended setup:

1. Install BlackHole 2ch.
2. Open Audio MIDI Setup.
3. Create a Multi-Output Device that includes the real speakers/headphones and
   BlackHole 2ch.
4. Select that Multi-Output Device as the macOS sound output.
5. Start CivilAI and confirm AiConnect shows `macos-virtual-loopback` ready.

Once configured, recording/transcription runs locally through the packaged
backend and local model cache.

## Model Setup

The app exposes Offline Models in AiConnect. Whisper model artifacts are pulled
from `ggerganov/whisper.cpp` with upstream hash verification. Qwen GGUF model
entries are available for local LLM testing, but SHA-256 metadata is not
published by the source repository, so the UI marks them accordingly.
