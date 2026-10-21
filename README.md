# IM 19 — Institutional RAG Foundation

IM 19 is being developed as a controlled AI marketing and institutional-knowledge system. This repository currently contains the first Dropbox → Supabase RAG integration scaffold.

## Current implementation boundary

Implemented in this repository:
- Dropbox source-file discovery and extraction for TXT, Markdown, HTML, PDF, and DOCX.
- Chunking and normalized embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
- Backend RPC calls to Supabase for document upsert, chunk replacement, health status, and semantic retrieval.
- A local preflight diagnostic to detect an out-of-date or incomplete Codespaces checkout without printing secrets.

Not yet proven / not to be assumed:
- A successful end-to-end ingestion from the user's Dropbox.
- Non-empty indexed documents or validated retrieval relevance.
- An application-runtime orchestrator that automatically routes a user request between a language model, GitHub tools, and Supabase. ChatGPT's connected GitHub/Supabase tools are integration surfaces for this conversation; they do not automatically become tools inside a deployed IM 19 application.
- Production readiness. Human review, access controls, evaluation, observability, and rollout approval remain required.

## Architecture today

```text
Dropbox source folder
        │ Dropbox API (read-only)
        ▼
IM 19 RAG integration (trusted backend / Codespaces)
  ├─ extract text → chunk → embed (384 dimensions)
  └─ call restricted Supabase RPCs using service-role credentials
        │
        ▼
Supabase: rag.documents + rag.document_chunks
        │ match_rag_chunks RPC
        ▼
Retrieved chunks with metadata/similarity
```

A future application orchestrator should call tools through explicit, narrowly scoped interfaces, validate outputs, preserve source attribution, apply authorization before retrieval, and log decisions. It must not expose the Supabase service-role key to a browser, model prompt, or client-side code.

## Recover a Codespaces checkout

The integration files exist on the GitHub `main` branch under `integrations/rag/`. If the Codespaces terminal says that folder does not exist, first inspect the checkout; do not reset or discard local work.

```bash
cd /workspaces/im19
pwd
git rev-parse --show-toplevel
git status --short --branch
git branch --show-current
git remote -v
git fetch origin
git status --short --branch
```

If there are **no local changes** and the current branch is `main`, synchronize with:

```bash
git pull --ff-only origin main
```

If there are local changes, a different branch, or Git refuses the pull, stop and inspect the status before deciding how to reconcile it. Do not run `git reset --hard`.

After syncing, verify the files:

```bash
ls -la integrations/rag
python scripts/rag_preflight.py
```

## Configure secrets safely

In Codespaces, configure these as Codespaces secrets or inject them through a trusted backend environment:

- `DROPBOX_ACCESS_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Optional settings: `DROPBOX_ROOT_PATH`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, and `CHUNK_OVERLAP`. The service-role key is backend-only. Never paste credentials into chat, commit them, or print them in logs. If a token was shared or exposed, revoke and rotate it.

A local `.env` may be used for development only and must stay untracked. Run `python scripts/rag_preflight.py --strict-config` to check file presence and whether required variable names have non-empty values; the script never prints values.

## Install and verify

Run from the repository root:

```bash
python -m pip install -r integrations/rag/requirements.txt
python -m integrations.rag.healthcheck
python -m integrations.rag.ingest --dry-run
```

The dry run still needs Dropbox read credentials but does not write to Supabase. Only after it succeeds should a maintainer deliberately run ingestion:

```bash
python -m integrations.rag.ingest
python -m integrations.rag.retrieve --query "What documents are indexed?" --top-k 5
```

Confirm that document/chunk counts are non-zero and that retrieval returns relevant source metadata. An empty source folder or an empty extraction result is not a successful knowledge index.

## Database migration history

The connector migration is present at `supabase/migrations/20261021000000_institutional_rag_connectors.sql`. The connected project has previously exposed the expected RPCs and RAG tables, but its recorded migration list did not include this migration. Before applying or repairing migration history, compare the SQL in the repository with the live function signatures, grants, RLS settings, and migration records. Do not blindly re-apply DDL or mark a migration as applied without a reviewed reconciliation plan.

## Local diagnostic tests

```bash
python -m unittest discover -s tests -v
```

The preflight tool is diagnostic only: it never fetches, pulls, modifies Git state, calls Dropbox/Supabase, or writes database records.
