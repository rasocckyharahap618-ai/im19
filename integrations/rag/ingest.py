"""Ingest Dropbox source files into Supabase pgvector. Backend use only."""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
from io import BytesIO
from pathlib import PurePosixPath

import dropbox
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from supabase import create_client

from integrations.rag.config import require_supabase_config
from integrations.rag.mining import assess_document, normalize_text, sha256_text

SUPPORTED = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf", ".docx"}
DEFAULT_MAX_FILE_BYTES = 25 * 1024 * 1024
EXPECTED_EMBEDDING_DIMENSION = 384


def validate_dropbox_root(root: str) -> str:
    """Validate an explicit Dropbox folder path; reject root-wide and traversal paths."""
    value = root.strip()
    path = PurePosixPath(value)
    if not value.startswith("/") or value == "/" or ".." in path.parts:
        raise ValueError("DROPBOX_ROOT_PATH must be a specific absolute folder path without '..' segments.")
    return str(path)


def max_file_bytes_from_env() -> int:
    raw = os.getenv("MAX_FILE_BYTES", str(DEFAULT_MAX_FILE_BYTES)).strip()
    try:
        limit = int(raw)
    except ValueError as exc:
        raise ValueError("MAX_FILE_BYTES must be a positive integer.") from exc
    if limit < 1:
        raise ValueError("MAX_FILE_BYTES must be a positive integer.")
    return limit


def validate_file_size(path: str, size: int | None, limit: int) -> None:
    """Reject oversized Dropbox metadata or downloaded content before extraction."""
    if limit < 1:
        raise ValueError("File size limit must be positive.")
    if size is not None and size > limit:
        raise ValueError(f"Source file exceeds MAX_FILE_BYTES and was skipped: {PurePosixPath(path).name}")


def validate_embedding_vectors(vectors, expected_dimension: int = EXPECTED_EMBEDDING_DIMENSION) -> None:
    """Validate vector count/dimensions and finite values before database writes."""
    if len(vectors) == 0:
        raise ValueError("Embedding model returned no vectors.")
    for index, vector in enumerate(vectors):
        if len(vector) != expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch at vector {index}: expected {expected_dimension}, got {len(vector)}."
            )
        if not all(math.isfinite(float(value)) for value in vector):
            raise ValueError(f"Embedding vector {index} contains non-finite values.")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def extract_text(path: str, raw: bytes) -> str:
    ext = PurePosixPath(path).suffix.lower()
    if ext in {".txt", ".md", ".markdown"}:
        return raw.decode("utf-8", errors="replace")
    if ext in {".html", ".htm"}:
        return BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    if ext == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    if ext == ".docx":
        doc = DocxDocument(BytesIO(raw))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            paragraphs.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
        return "\n".join(paragraphs)
    return ""


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("Require CHUNK_SIZE > 0 and 0 <= CHUNK_OVERLAP < CHUNK_SIZE")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def list_source_files(client: dropbox.Dropbox, root: str) -> list[dict]:
    result = client.files_list_folder(root, recursive=True)
    entries = list(result.entries)
    while result.has_more:
        result = client.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)
    files = []
    for entry in entries:
        path = getattr(entry, "path_display", None) or getattr(entry, "path_lower", "")
        if isinstance(entry, dropbox.files.FileMetadata) and PurePosixPath(path).suffix.lower() in SUPPORTED:
            files.append({
                "path": path,
                "rev": entry.rev,
                "modified": entry.server_modified.isoformat() if entry.server_modified else None,
                "size": entry.size,
            })
    return files


def download_file(client: dropbox.Dropbox, path: str) -> bytes:
    _metadata, response = client.files_download(path)
    return response.content


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Parse/chunk only; do not write to Supabase")
    args = parser.parse_args()

    dbx = dropbox.Dropbox(oauth2_access_token=require_env("DROPBOX_ACCESS_TOKEN"))
    root = validate_dropbox_root(os.getenv("DROPBOX_ROOT_PATH", "/Institutional_RAG/01_RAW_SOURCES"))
    max_file_bytes = max_file_bytes_from_env()
    files = list_source_files(dbx, root)
    print(f"Found {len(files)} supported files under {root}")
    if not files:
        raise RuntimeError(
            "No supported source files were found. Check DROPBOX_ROOT_PATH, Dropbox folder access, "
            "the files.content.read/files.metadata.read scopes, and supported file extensions."
        )

    chunk_size = int(os.getenv("CHUNK_SIZE", "900"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "120"))
    # Validate chunk settings before downloading or writing anything.
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require CHUNK_SIZE > 0 and 0 <= CHUNK_OVERLAP < CHUNK_SIZE")

    if args.dry_run:
        parsed_files = 0
        total_chunks = 0
        for item in files:
            validate_file_size(item["path"], item.get("size"), max_file_bytes)
            raw = download_file(dbx, item["path"])
            validate_file_size(item["path"], len(raw), max_file_bytes)
            text = normalize_text(extract_text(item["path"], raw))
            quality = assess_document(text)
            if not quality.accepted:
                print(f"SKIP quality gate: {item['path']} reasons={','.join(quality.reasons)}")
                continue
            chunks = chunk_text(text, chunk_size, overlap)
            if not chunks:
                print(f"SKIP empty/unextractable: {item['path']}")
                continue
            parsed_files += 1
            total_chunks += len(chunks)
            print(f'{item["path"]}: bytes={len(raw)} chars={len(text)} chunks={len(chunks)}')
        if total_chunks == 0:
            raise RuntimeError("Dry run extracted zero chunks. No database writes were performed.")
        print(f"DRY RUN OK: parsed_files={parsed_files}, chunks={total_chunks}; no database writes performed.")
        return

    supabase_url, service_key = require_supabase_config()
    supabase = create_client(supabase_url, service_key)
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
    if not model_name:
        raise RuntimeError("EMBEDDING_MODEL cannot be empty.")
    model = SentenceTransformer(model_name)
    model_dimension = model.get_sentence_embedding_dimension()
    if model_dimension != EXPECTED_EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Embedding model dimension mismatch: database RPC expects {EXPECTED_EMBEDDING_DIMENSION}, "
            f"configured model reports {model_dimension}."
        )

    indexed_files = 0
    indexed_chunks = 0
    for item in files:
        path = item["path"]
        validate_file_size(path, item.get("size"), max_file_bytes)
        raw = download_file(dbx, path)
        validate_file_size(path, len(raw), max_file_bytes)
        text = normalize_text(extract_text(path, raw))
        quality = assess_document(text)
        if not quality.accepted:
            print(f"SKIP quality gate: {path} reasons={','.join(quality.reasons)}")
            continue
        digest = sha256_text(text)
        chunks = chunk_text(text, chunk_size, overlap)
        if not chunks:
            print(f"SKIP empty/unextractable: {path}")
            continue

        # Finish extraction and embedding validation before creating/updating any database record.
        vectors = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        validate_embedding_vectors(vectors)

        document = {
            "p_source_uri": path,
            "p_source_version": item["rev"],
            "p_title": PurePosixPath(path).name,
            "p_content_hash": digest,
            "p_metadata": {
                "source": "dropbox",
                "size_bytes": item["size"],
                "embedding_model": model_name,
                "pipeline_version": "im19-institutional-rag-mining-v1",
                "character_count": quality.character_count,
                "word_count": quality.word_count,
                "quality_accepted": quality.accepted,
            },
        }
        saved = supabase.rpc("upsert_rag_document", document).execute()
        data = saved.data
        if isinstance(data, list):
            data = data[0] if data else None
        if isinstance(data, dict):
            data = data.get("upsert_rag_document") or data.get("id")
        document_id = data
        if not document_id:
            raise RuntimeError(f"Supabase did not return a document id for source file {PurePosixPath(path).name}.")

        chunk_rows = [
            {
                "chunk_index": i,
                "content": chunk,
                "content_hash": hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                "token_count": None,
                "embedding": vector.tolist(),
                "embedding_model": model_name,
                "metadata": {
                    "source_uri": path,
                    "source_provider": "dropbox",
                    "document_hash": digest,
                    "pipeline_version": "im19-institutional-rag-mining-v1",
                },
            }
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        replaced = supabase.rpc("replace_rag_document_chunks", {
            "p_document_id": document_id,
            "p_chunks": chunk_rows,
        }).execute()
        if replaced.data is not None and int(replaced.data) != len(chunk_rows):
            raise RuntimeError(
                f"Chunk replacement count mismatch for {path}: expected {len(chunk_rows)}, got {replaced.data}."
            )
        indexed_files += 1
        indexed_chunks += len(chunk_rows)
        print(f"INGESTED {path}: {len(chunks)} chunks sha256={digest[:12]}")

    if indexed_chunks == 0:
        raise RuntimeError("Ingestion completed without indexing any chunks. Check source extraction and file contents.")
    print(f"Ingestion complete: files={indexed_files}, chunks={indexed_chunks}.")
    print("Run a retrieval query and verify returned content and source metadata before treating the index as ready.")


if __name__ == "__main__":
    main()
