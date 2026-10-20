"""Ingest Dropbox source files into Supabase pgvector. Backend use only."""
from __future__ import annotations

import argparse
import hashlib
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

SUPPORTED = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf", ".docx"}


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
    root = os.getenv("DROPBOX_ROOT_PATH", "/Institutional_RAG/01_RAW_SOURCES").strip()
    if not root.startswith("/"):
        raise RuntimeError("DROPBOX_ROOT_PATH must be an absolute Dropbox path beginning with '/'.")
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
            raw = download_file(dbx, item["path"])
            text = extract_text(item["path"], raw)
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

    indexed_files = 0
    indexed_chunks = 0
    for item in files:
        path = item["path"]
        raw = download_file(dbx, path)
        digest = hashlib.sha256(raw).hexdigest()
        text = extract_text(path, raw)
        chunks = chunk_text(text, chunk_size, overlap)
        if not chunks:
            print(f"SKIP empty/unextractable: {path}")
            continue

        document = {
            "p_source_uri": path,
            "p_source_version": item["rev"],
            "p_title": PurePosixPath(path).name,
            "p_content_hash": digest,
            "p_metadata": {"source": "dropbox", "size_bytes": item["size"], "embedding_model": model_name},
        }
        saved = supabase.rpc("upsert_rag_document", document).execute()
        data = saved.data
        if isinstance(data, list):
            data = data[0] if data else None
        if isinstance(data, dict):
            data = data.get("upsert_rag_document") or data.get("id")
        document_id = data
        if not document_id:
            raise RuntimeError(f"Supabase did not return a document id for source file {path}.")

        vectors = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        chunk_rows = [
            {
                "chunk_index": i,
                "content": chunk,
                "content_hash": hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                "token_count": None,
                "embedding": vector.tolist(),
                "embedding_model": model_name,
                "metadata": {"source_uri": path, "source_provider": "dropbox", "document_hash": digest},
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
