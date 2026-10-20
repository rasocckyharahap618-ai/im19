"""Ingest Dropbox source files into Supabase pgvector. Backend use only."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import PurePosixPath

import dropbox
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from supabase import create_client

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
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("Require CHUNK_SIZE > 0 and 0 <= CHUNK_OVERLAP < CHUNK_SIZE")
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
    files = list_source_files(dbx, root)
    print(f"Found {len(files)} supported files under {root}")
    if args.dry_run:
        for item in files:
            raw = download_file(dbx, item["path"])
            text = extract_text(item["path"], raw)
            chunks = chunk_text(text, int(os.getenv("CHUNK_SIZE", "900")), int(os.getenv("CHUNK_OVERLAP", "120")))
            print(f'{item["path"]}: bytes={len(raw)} chars={len(text)} chunks={len(chunks)}')
        print("DRY RUN: no database writes performed.")
        return

    supabase_url = require_env("SUPABASE_URL")
    service_key = require_env("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(supabase_url, service_key)
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)
    chunk_size = int(os.getenv("CHUNK_SIZE", "900"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "120"))

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
            "source_path": path,
            "title": PurePosixPath(path).name,
            "content_sha256": digest,
            "source_revision": item["rev"],
            "source_modified_at": item["modified"],
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "dropbox", "size_bytes": item["size"], "model": model_name},
        }
        saved = supabase.table("rag_documents").upsert(document, on_conflict="source_path").execute()
        if not saved.data:
            raise RuntimeError(f"Supabase did not return document row for {path}")
        document_id = saved.data[0]["id"]

        vectors = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        chunk_rows = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk,
                "embedding": vector.tolist(),
                "metadata": {"source_path": path, "content_sha256": digest},
            }
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        # Delete old chunks only after parsing/embedding succeeded; then write the new version.
        supabase.table("rag_chunks").delete().eq("document_id", document_id).execute()
        for offset in range(0, len(chunk_rows), 100):
            supabase.table("rag_chunks").upsert(
                chunk_rows[offset:offset + 100],
                on_conflict="document_id,chunk_index",
            ).execute()
        print(f"INGESTED {path}: {len(chunks)} chunks sha256={digest[:12]}")

    print("Ingestion complete. Run the SQL count/retrieval checks documented in README.")


if __name__ == "__main__":
    main()
