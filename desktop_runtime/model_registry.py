"""Known offline model options for first-launch downloads.

Models are intentionally not bundled with the installer. This registry keeps
display metadata, target filenames, and checksums together so downloader and UI
code can share the same source of truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .app_paths import models_dir


ModelKind = Literal["stt", "llm"]


@dataclass(frozen=True)
class ModelSpec:
    id: str
    kind: ModelKind
    label: str
    filename: str
    size_mb: int
    min_ram_gb: int
    checksum: str
    url: str
    checksum_algorithm: str = "sha256"

    @property
    def path(self) -> Path:
        return models_dir() / self.filename


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "whisper-tiny-en": ModelSpec(
        id="whisper-tiny-en",
        kind="stt",
        label="Whisper tiny.en",
        filename="ggml-tiny.en.bin",
        size_mb=75,
        min_ram_gb=2,
        checksum="c78c86eb1a8faa21b369bcd33207cc90d64ae9df",
        checksum_algorithm="sha1",
        url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
    ),
    "whisper-base-en": ModelSpec(
        id="whisper-base-en",
        kind="stt",
        label="Whisper base.en",
        filename="ggml-base.en.bin",
        size_mb=140,
        min_ram_gb=4,
        checksum="137c40403d78fd54d454da0f9bd998f78703390c",
        checksum_algorithm="sha1",
        url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin",
    ),
    "whisper-small-en": ModelSpec(
        id="whisper-small-en",
        kind="stt",
        label="Whisper small.en",
        filename="ggml-small.en.bin",
        size_mb=460,
        min_ram_gb=8,
        checksum="db8a495a91d927739e50b3fc1cc4c6b8f6c2d022",
        checksum_algorithm="sha1",
        url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin",
    ),
    "qwen2.5-0.5b-q4": ModelSpec(
        id="qwen2.5-0.5b-q4",
        kind="llm",
        label="Qwen2.5 0.5B Instruct Q4_K_M",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        size_mb=469,
        min_ram_gb=4,
        checksum="",
        url="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    ),
    "qwen2.5-1.5b-q4": ModelSpec(
        id="qwen2.5-1.5b-q4",
        kind="llm",
        label="Qwen2.5 1.5B Instruct Q4_K_M",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        size_mb=1066,
        min_ram_gb=8,
        checksum="",
        url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    ),
}


def list_models(kind: ModelKind | None = None) -> list[ModelSpec]:
    models = list(MODEL_REGISTRY.values())
    if kind is not None:
        models = [model for model in models if model.kind == kind]
    return models


def get_model(model_id: str) -> ModelSpec:
    try:
        return MODEL_REGISTRY[model_id]
    except KeyError as exc:
        raise ValueError(f"Unknown model id: {model_id}") from exc
