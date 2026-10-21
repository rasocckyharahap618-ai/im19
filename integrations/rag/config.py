"""Safe configuration validation for the IM 19 RAG backend."""
from __future__ import annotations

import os
from urllib.parse import urlsplit


def require_supabase_config() -> tuple[str, str]:
    """Return a validated Supabase API URL and backend key without logging either."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url:
        raise RuntimeError("SUPABASE_URL is missing. Set it to the project API URL in Codespaces secrets.")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing. Set the backend-only key in Codespaces secrets.")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        # Accessing .port can raise ValueError for a malformed port.
        _ = parsed.port
    except ValueError as exc:
        raise RuntimeError(
            "SUPABASE_URL is malformed. Use the project API URL, for example "
            "https://<project-ref>.supabase.co, without quotes or extra paths."
        ) from exc

    local_http = parsed.scheme == "http" and hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not hostname
        or (parsed.scheme != "https" and not local_http)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise RuntimeError(
            "SUPABASE_URL must be the base project URL (HTTPS, no credentials, query, fragment, "
            "or paths such as /rest/v1). Example: https://<project-ref>.supabase.co. "
            "The configured value is not printed for safety."
        )

    return url.rstrip("/"), key
