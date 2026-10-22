"""Read-only live readiness check for the IM 19 Dropbox → Supabase RAG."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

import dropbox
from dotenv import load_dotenv
from supabase import create_client

from integrations.rag.config import require_supabase_config
from integrations.rag.readiness import (
    DEFAULT_DROPBOX_ROOT,
    DEFAULT_MAX_FILE_BYTES,
    classify_source_file,
    parse_health_payload,
    validate_source_root,
)

EXPECTED_EMBEDDING_DIMENSION = 384


def max_file_bytes_from_env() -> int:
    raw = os.getenv("MAX_FILE_BYTES", str(DEFAULT_MAX_FILE_BYTES)).strip()
    try:
        limit = int(raw)
    except ValueError as exc:
        raise ValueError("MAX_FILE_BYTES must be a positive integer.") from exc
    if limit < 1:
        raise ValueError("MAX_FILE_BYTES must be a positive integer.")
    return limit


def summarize_dropbox_source(
    client: dropbox.Dropbox, root: str, max_file_bytes: int
) -> dict[str, int]:
    """List the configured folder only; never download or print source contents."""
    result = client.files_list_folder(root, recursive=True)
    entries = list(result.entries)
    while result.has_more:
        result = client.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)

    summary = {"supported_files": 0, "usable_files": 0, "oversized_files": 0}
    for entry in entries:
        if not isinstance(entry, dropbox.files.FileMetadata):
            continue
        path = getattr(entry, "path_display", None) or entry.name
        classification = classify_source_file(path, entry.size, max_file_bytes)
        if classification == "unsupported":
            continue
        summary["supported_files"] += 1
        if classification == "oversized":
            summary["oversized_files"] += 1
        else:
            summary["usable_files"] += 1
    return summary


def main() -> None:
    load_dotenv()
    failures: list[str] = []

    token = os.getenv("DROPBOX_ACCESS_TOKEN", "").strip()
    if not token:
        print("Dropbox ERROR: DROPBOX_ACCESS_TOKEN is missing.")
        failures.append("Dropbox token is not configured.")
    else:
        try:
            root = validate_source_root(
                os.getenv("DROPBOX_ROOT_PATH", DEFAULT_DROPBOX_ROOT)
            )
            max_file_bytes = max_file_bytes_from_env()
            dbx = dropbox.Dropbox(oauth2_access_token=token)
            source = summarize_dropbox_source(dbx, root, max_file_bytes)
            print(
                "Dropbox API OK: "
                f"source_folder={root}; "
                f"supported_files={source['supported_files']}; "
                f"usable_files={source['usable_files']}; "
                f"oversized_files={source['oversized_files']}"
            )
            if source["usable_files"] == 0:
                failures.append(
                    "The source folder has no usable supported files. Add TXT/Markdown/HTML/PDF/DOCX files "
                    "or correct DROPBOX_ROOT_PATH and access scopes."
                )
        except Exception as exc:
            # SDK errors may contain request metadata; report type only, never raw exception details.
            print(f"Dropbox ERROR: source listing failed ({type(exc).__name__}); details withheld.")
            failures.append("Dropbox source folder could not be listed.")

    try:
        url, key = require_supabase_config()
        hostname = urlsplit(url).hostname or "(unknown)"
        project_ref = hostname.split(".", 1)[0]
        client = create_client(url, key)

        health_response = client.rpc("rag_connector_health").execute()
        counts = parse_health_payload(health_response.data)

        # A zero vector is a read-only contract probe. It does not write data or load model weights.
        retrieval_response = client.rpc(
            "match_rag_chunks",
            {
                "query_embedding": [0.0] * EXPECTED_EMBEDDING_DIMENSION,
                "match_count": 1,
                "filter_metadata": {},
            },
        ).execute()
        if not isinstance(retrieval_response.data, list):
            raise ValueError("match_rag_chunks returned an unexpected payload.")

        print(
            "Supabase RPC OK: "
            f"project_ref={project_ref}; "
            f"documents={counts['documents']}; "
            f"chunks={counts['chunks']}; "
            "match_rag_chunks=reachable"
        )
        if counts["documents"] == 0 or counts["chunks"] == 0:
            failures.append(
                "The RAG index is empty or incomplete (documents/chunks count is zero). "
                "Ingestion and retrieval readiness are not yet proven."
            )
    except RuntimeError as exc:
        # require_supabase_config() emits safe diagnostics containing setting names, never values.
        print(f"Supabase CONFIG ERROR: {exc}")
        failures.append("Supabase configuration is incomplete or invalid.")
    except Exception as exc:
        print(f"Supabase ERROR: read-only RPC checks failed ({type(exc).__name__}); details withheld.")
        failures.append("Supabase RPC contract or connectivity check failed.")

    if failures:
        print("\nRAG NOT READY:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(2)

    print(
        "\nRAG connectivity and corpus-readiness checks passed. "
        "Run ingestion with --dry-run and evaluate real retrieval results before production use."
    )


if __name__ == "__main__":
    main()
