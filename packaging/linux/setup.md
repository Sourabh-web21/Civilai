# CivilAI Linux Setup

## Install

Use the `.AppImage` for a portable install, or the `.deb` for Debian/Ubuntu.
Choose x86_64 or ARM64 to match the machine.

```bash
chmod +x CivilAI_*.AppImage
./CivilAI_*.AppImage
```

Or:

```bash
sudo apt install ./CivilAI_*.deb
```

For meeting capture, PipeWire or PulseAudio must expose a monitor/loopback
source for the active output. Confirm status in AiConnect.

## Build

```bash
chmod +x packaging/linux/build_linux.sh
./packaging/linux/build_linux.sh
```

Artifacts are under `desktop/src-tauri/target/release/bundle/`.

## Share

Share one `.AppImage` or `.deb` per target architecture. Do not share `.env`,
`venv`, databases, logs, or model caches. Users download models from AiConnect.
