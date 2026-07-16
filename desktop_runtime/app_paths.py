"""Cross-platform application data paths for desktop packaging.

The web/dev workflow keeps using repository-local files by default. Packaged
desktop builds can opt in with CIVILAI_DESKTOP=1 so mutable state is never
written inside the installation directory.
"""
from __future__ import annotations

import os
import platform
from pathlib import Path


APP_NAME = os.getenv("CIVILAI_APP_NAME", "CivilAI")


def is_desktop_mode() -> bool:
    return os.getenv("CIVILAI_DESKTOP", "").strip().lower() in {"1", "true", "yes", "on"}


def app_data_dir(app_name: str = APP_NAME) -> Path:
    system = platform.system().lower()
    if system == "windows":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / app_name
    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    xdg_data = os.getenv("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
    return base / app_name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_path(*parts: str) -> Path:
    return ensure_dir(app_data_dir()).joinpath(*parts)


def sqlite_path(filename: str = "civilai.sqlite3") -> Path:
    return data_path(filename)


def media_root() -> Path:
    return ensure_dir(data_path("media"))


def logs_dir() -> Path:
    return ensure_dir(data_path("logs"))


def models_dir() -> Path:
    return ensure_dir(data_path("models"))


def exports_dir() -> Path:
    return ensure_dir(data_path("exports"))

