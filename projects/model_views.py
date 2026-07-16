from dataclasses import asdict, dataclass
import threading

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from desktop_runtime.downloads import download_model, is_model_present
from desktop_runtime.model_registry import get_model, list_models
from utils.response_utils import CivilErrorResponse, CivilResponse

from .models import OfflineModelSetting


@dataclass
class DownloadJob:
    model_id: str
    status: str = "queued"
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error: str = ""
    path: str = ""


_download_jobs: dict[str, DownloadJob] = {}
_download_lock = threading.Lock()


def serialize_model(model):
    return {
        "id": model.id,
        "kind": model.kind,
        "label": model.label,
        "filename": model.filename,
        "size_mb": model.size_mb,
        "min_ram_gb": model.min_ram_gb,
        "checksum": model.checksum,
        "checksum_algorithm": model.checksum_algorithm,
        "sha256_verified": bool(model.checksum and model.checksum_algorithm == "sha256"),
        "download_configured": bool(model.url),
        "downloaded": is_model_present(model),
        "path": str(model.path) if is_model_present(model) else "",
    }


class OfflineModelListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        kind = request.query_params.get("kind") or None
        if kind not in {None, "stt", "llm"}:
            return CivilErrorResponse({"error": "kind must be stt or llm."}, status=status.HTTP_400_BAD_REQUEST)
        return CivilResponse(
            [serialize_model(model) for model in list_models(kind)],
            status=status.HTTP_200_OK,
            is_success="Offline models",
        )


class OfflineModelDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, model_id):
        try:
            model = get_model(model_id)
        except ValueError as exc:
            return CivilErrorResponse({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        with _download_lock:
            job = _download_jobs.get(model_id)
            job_payload = asdict(job) if job else None
        return CivilResponse(
            {
                "model": serialize_model(model),
                "job": job_payload,
            },
            status=status.HTTP_200_OK,
            is_success="Model download status",
        )

    def post(self, request, model_id):
        try:
            model = get_model(model_id)
        except ValueError as exc:
            return CivilErrorResponse({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not model.url:
            return CivilErrorResponse(
                {"error": f"Model {model.id} does not have a download URL configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_model_present(model):
            OfflineModelSetting.objects.update_or_create(
                kind=model.kind,
                defaults={
                    "model_id": model.id,
                    "model_path": str(model.path),
                    "is_downloaded": True,
                    "checksum_sha256": model.checksum if model.checksum_algorithm == "sha256" else "",
                    "settings": {"checksum": model.checksum, "checksum_algorithm": model.checksum_algorithm},
                },
            )
            return CivilResponse(
                {"model": serialize_model(model), "job": None},
                status=status.HTTP_200_OK,
                is_success="Model already downloaded",
            )

        with _download_lock:
            existing = _download_jobs.get(model.id)
            if existing and existing.status in {"queued", "downloading", "verifying"}:
                return CivilResponse(
                    {"model": serialize_model(model), "job": asdict(existing)},
                    status=status.HTTP_202_ACCEPTED,
                    is_success="Model download already running",
                )
            job = DownloadJob(model_id=model.id)
            _download_jobs[model.id] = job

        thread = threading.Thread(target=_download_worker, args=(model.id,), daemon=True)
        thread.start()
        return CivilResponse(
            {"model": serialize_model(model), "job": asdict(job)},
            status=status.HTTP_202_ACCEPTED,
            is_success="Model download started",
        )


def _download_worker(model_id: str):
    model = get_model(model_id)

    def on_progress(downloaded, total):
        with _download_lock:
            job = _download_jobs[model_id]
            job.status = "downloading"
            job.downloaded_bytes = downloaded
            job.total_bytes = total

    try:
        with _download_lock:
            _download_jobs[model_id].status = "downloading"
        path = download_model(model, progress=on_progress)
        with _download_lock:
            job = _download_jobs[model_id]
            job.status = "complete"
            job.path = str(path)
            job.downloaded_bytes = path.stat().st_size
            job.total_bytes = job.downloaded_bytes
        OfflineModelSetting.objects.update_or_create(
            kind=model.kind,
            defaults={
                "model_id": model.id,
                "model_path": str(path),
                "is_downloaded": True,
                "checksum_sha256": model.checksum if model.checksum_algorithm == "sha256" else "",
                "settings": {"checksum": model.checksum, "checksum_algorithm": model.checksum_algorithm},
            },
        )
    except Exception as exc:
        with _download_lock:
            job = _download_jobs[model_id]
            job.status = "failed"
            job.error = str(exc)
