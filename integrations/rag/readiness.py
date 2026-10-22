"""Pure readiness helpers shared by live checks and offline tests."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

DEFAULT_DROPBOX_ROOT = "/Institutional_RAG/01_RAW_SOURCES"
DEFAULT_MAX_FILE_BYTES = 25 * 1024 * 1024
SUPPORTED_EXTENSIONS = frozenset(
    {".txt", ".md", ".markdown", ".html", ".htm", ".pdf", ".docx"}
)


def validate_source_root(root: str) -> str:
    """Require a specific absolute Dropbox folder, never account-wide root/traversal."""
    value = root.strip()
    path = PurePosixPath(value)
    if not value.startswith("/") or value in {"", "/"} or ".." in path.parts:
        raise ValueError(
            "DROPBOX_ROOT_PATH must be a specific absolute folder path without '..' segments."
        )
    return str(path)


def classify_source_file(path: str, size: int | None, max_file_bytes: int) -> str:
    """Return 'supported', 'oversized', or 'unsupported' without reading file contents."""
    if max_file_bytes < 1:
        raise ValueError("MAX_FILE_BYTES must be a positive integer.")
    if size is not None and size < 0:
        raise ValueError("Dropbox file size cannot be negative.")
    if PurePosixPath(path).suffix.lower() not in SUPPORTED_EXTENSIONS:
        return "unsupported"
    if size is not None and size > max_file_bytes:
        return "oversized"
    return "supported"


def parse_health_payload(payload: Any) -> dict[str, int]:
    """Validate the read-only rag_connector_health RPC payload."""
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError("rag_connector_health returned an unexpected payload.")
    counts: dict[str, int] = {}
    for field in ("documents", "chunks"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"rag_connector_health returned an invalid {field} count.")
        counts[field] = value
    return counts
