"""Checksum helpers for offline model downloads."""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import Callable

from .model_registry import ModelSpec


def checksum_file(path: Path, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    return checksum_file(path, "sha256", chunk_size=chunk_size)


def is_model_present(model: ModelSpec) -> bool:
    if not model.path.is_file():
        return False
    if not model.checksum:
        return True
    return checksum_file(model.path, model.checksum_algorithm).lower() == model.checksum.lower()


def download_model(model: ModelSpec, progress: Callable[[int, int], None] | None = None) -> Path:
    if not model.url:
        raise ValueError(f"Model {model.id} does not have a download URL configured.")
    model.path.parent.mkdir(parents=True, exist_ok=True)
    partial = model.path.with_suffix(model.path.suffix + ".part")
    downloaded = partial.stat().st_size if partial.exists() else 0
    headers = {}
    if downloaded:
        headers["Range"] = f"bytes={downloaded}-"
    request = urllib.request.Request(model.url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        total_header = response.headers.get("Content-Length")
        total = int(total_header) + downloaded if total_header else 0
        mode = "ab" if downloaded else "wb"
        with partial.open(mode) as file_obj:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file_obj.write(chunk)
                downloaded += len(chunk)
                if progress:
                    progress(downloaded, total)
    if model.checksum:
        actual = checksum_file(partial, model.checksum_algorithm)
        if actual.lower() != model.checksum.lower():
            raise ValueError("Downloaded model checksum verification failed.")
    partial.replace(model.path)
    return model.path
