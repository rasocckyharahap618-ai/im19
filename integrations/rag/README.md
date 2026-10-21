# IM 19 — Dropbox → Supabase Institutional RAG

This integration runs in GitHub Codespaces (or another trusted backend). Dropbox is the source of truth for source files; the existing institutional schema `rag.documents` and `rag.document_chunks` store document metadata, chunk text, and embeddings. It reuses the institutional RAG schema rather than creating a parallel document store.

## Data flow

1. Read supported files under `/Institutional_RAG/01_RAW_SOURCES` using the Dropbox API.
2. Extract text from TXT, Markdown, HTML, PDF, and DOCX.
3. Split text into overlapping chunks and create embeddings with `sentence-transformers/all-MiniLM-L6-v2`.
4. Upsert document metadata and chunks into Supabase.
5. Retrieve relevant chunks through the `match_rag_chunks` RPC.

## Configure Codespaces secrets

Add these as **Codespaces secrets** (never commit real values):

- `DROPBOX_ACCESS_TOKEN` — Dropbox API token with read access to source files.
- `DROPBOX_ROOT_PATH` — default `/Institutional_RAG/01_RAW_SOURCES`.
- `SUPABASE_URL` — project API URL.
- `SUPABASE_SERVICE_ROLE_KEY` — backend-only secret key. Never use in browser/client-side code.
- Optional: `EMBEDDING_MODEL` — defaults to `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, matching the current RPC).
- Optional: `CHUNK_SIZE` and `CHUNK_OVERLAP` — chunking controls; overlap must be smaller than chunk size.
- Optional: `MAX_FILE_BYTES` — maximum source file size; defaults to 25 MiB.

The Dropbox token must be able to list and download files from the configured folder. Prefer a least-privilege Dropbox app/folder access. Rotate credentials if exposed. The integration uses restricted public RPC functions, so the `rag` schema does not need to be exposed through the Data API. The functions are executable only by `service_role`; keep that key backend-only.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r integrations/rag/requirements.txt
cp integrations/rag/.env.example .env
# Fill .env locally only; do not commit it.
python -m integrations.rag.ingest --dry-run
python -m integrations.rag.ingest
```

For Codespaces, prefer repository/org Codespaces secrets over a committed `.env`. Install optional PDF/DOCX dependencies listed in requirements.

## Verify

```bash
python -m integrations.rag.healthcheck
python -m integrations.rag.ingest --dry-run
python -m integrations.rag.retrieve --query "What are the institutional RAG ingestion rules?" --top-k 5
```

A dry run lists supported files and parses/chunks them without writing to Supabase. It still downloads source content from Dropbox. The default `MAX_FILE_BYTES` limit is 25 MiB per file; oversized files fail closed rather than being extracted. A normal run writes to the database. First model load downloads model weights, so initial run may take several minutes.

## Security and data-integrity boundaries

- `retrieve.py` is an operator CLI using a backend key. Do not expose it directly as a user-facing endpoint. The current RPC filter is metadata filtering, not per-user authorization. Before serving multiple users or tenants, implement and test identity-bound document authorization in the trusted backend and database design.
- The current connector migration upserts on `(source_uri, content_hash)`. A changed file may therefore create a new document record while an older version remains. Reconcile this with the actual core schema and retention policy before claiming clean version replacement; do not change live DDL blindly.
- Document upsert and chunk replacement are separate RPC calls, not a single atomic transaction. A failure between calls can leave partial state. Treat live ingestion as a controlled operator action until a transactional database RPC and recovery tests are implemented.

## Important status

This is an integration scaffold, not proof of a successful live ingestion. Configure secrets, reconcile the SQL migration with the target project, run offline tests and healthcheck, then run a dry-run and verify document/chunk counts plus retrieval relevance. No Dropbox or Supabase credentials are stored in this repository.
