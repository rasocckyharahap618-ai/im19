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
- `SUPABASE_URL` — API URL for the intended Supabase project.
- `SUPABASE_SERVICE_ROLE_KEY` — backend-only secret key. Never use in browser/client-side code.
- Optional: `EMBEDDING_MODEL` — defaults to `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, matching the current RPC).
- Optional: `CHUNK_SIZE` and `CHUNK_OVERLAP` — chunking controls; overlap must be smaller than chunk size.
- Optional: `MAX_FILE_BYTES` — maximum source file size; defaults to 25 MiB.

The Dropbox token must be able to list and download files from the configured folder. Prefer a least-privilege Dropbox app/folder access. Rotate credentials if exposed. The integration uses restricted public RPC functions, so the `rag` schema does not need to be exposed through the Data API. The functions are executable only by `service_role`; keep that key backend-only.

**Project identity must match:** `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` must belong to the same intended Supabase project. Do not infer that two different project references are interchangeable. Verify the endpoint's project reference before running ingestion.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r integrations/rag/requirements.txt
cp integrations/rag/.env.example .env
# Fill .env locally only; do not commit it.
python -m integrations.rag.healthcheck
python -m integrations.rag.ingest --dry-run
```

For Codespaces, prefer repository/org Codespaces secrets over a committed `.env`. Install optional PDF/DOCX dependencies listed in requirements.

## Read-only readiness check

`python -m integrations.rag.healthcheck` now checks all of the following without writing to Supabase or downloading source documents:

- the configured Dropbox folder can be listed;
- at least one supported, under-limit source file is present;
- the Supabase health RPC returns valid document/chunk counts;
- the read-only `match_rag_chunks` RPC is reachable;
- the live index has both documents and chunks.

A source folder or index with zero records is reported as **not ready**, not as a successful RAG deployment. The check reports only a Dropbox folder path, file counts, the Supabase project reference, and status; it never prints tokens or raw source contents. The retrieval contract probe uses a zero vector and does not load embedding-model weights or write data.

A readiness pass is necessary but not sufficient for production: first run `python -m integrations.rag.ingest --dry-run`, then inspect actual retrieval quality and source citations.

## Safety and data-integrity boundaries

- Discover files only beneath the configured Dropbox source folder; do not crawl the entire account.
- Verify the intended Supabase project and compare database migration history with the actual deployed schema before applying SQL. An RPC missing from migration history is not proof that it is absent, and a function's presence is not proof that its migration history is reconciled. Do not blindly reapply SQL.
- The current connector migration upserts on `(source_uri, content_hash)`. A changed file may therefore create a new document record while an older version remains. Reconcile this with the actual core schema and retention policy before claiming clean version replacement.
- Document upsert and chunk replacement are separate RPC calls, not a single atomic transaction. A failure between calls can leave partial state. Treat live ingestion as a controlled operator action until a transactional database RPC and recovery tests are implemented.
- Keep the service-role key server-side only. Never expose it to browser code, MCP tool output, logs, or prompts.
- The current metadata filter is not per-user authorization. Before serving multiple users or tenants, implement and test identity-bound document authorization.
- Add retries/backoff, bounded concurrency, ingestion checkpointing, and dead-letter handling before large-scale corpus mining.
- Treat retrieved documents as untrusted data, not instructions to privileged agents. Review copyright, licensing, retention, and source permissions for each corpus.
- Use a reviewed pull request and staging corpus before production ingestion.

## Evaluation

Evaluation numbers are meaningful only when cases and retrieved results came from the intended corpus and were reviewed.

```bash
python scripts/rag_evaluate_jsonl.py --input tests/fixtures/rag_eval_results.jsonl --k 5
```
