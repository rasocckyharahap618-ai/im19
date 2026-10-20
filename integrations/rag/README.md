# IM 19 — Dropbox → Supabase Institutional RAG

This integration runs in GitHub Codespaces (or another trusted backend). Dropbox is the source of truth for source files; the existing institutional schema `rag.documents` and `rag.document_chunks` store document metadata, chunk text, and embeddings. It reuses the institutional RAG schema rather than creating a parallel document store.

## Data flow

1. Read supported files under `/Institutional_RAG/01_RAW_SOURCES` using the Dropbox API.
2. Extract text from TXT, Markdown, HTML, PDF, and DOCX.
3. Split text into overlapping chunks and create embeddings with `sentence-transformers/all-MiniLM-L6-v2`.
4. Upsert document metadata and chunks into Supabase.
5. Retrieve relevant chunks through the `match_rag_chunks` RPC.

## Configure Codespaces secrets

1. Open the repository **Settings → Secrets and variables → Codespaces**.
2. Select **New repository secret** for each required secret below. If you use organization-level secrets, confirm this repository is allowed to access them.
3. Rebuild/restart the Codespace terminal session after adding secrets if the environment does not expose the new values. Do not paste secret values into Copilot/OpenCode prompts, terminal output, issues, or logs.

Required secrets:

- `DROPBOX_ACCESS_TOKEN` — Dropbox API token with permission to list and download source files.
- `SUPABASE_URL` — Supabase project URL (for example, the project's `https://<project-ref>.supabase.co` URL).
- `SUPABASE_SERVICE_ROLE_KEY` — backend-only service-role secret. Never use it in browser/client-side code, `NEXT_PUBLIC_*` variables, commits, or screenshots.

Optional environment variables (set as Codespaces secrets/variables or in the terminal session):

- `DROPBOX_ROOT_PATH` — defaults to `/Institutional_RAG/01_RAW_SOURCES`.
- `EMBEDDING_MODEL` — defaults to `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions; must match the database vector dimension).
- `CHUNK_SIZE` — defaults to `900` characters.
- `CHUNK_OVERLAP` — defaults to `120` characters.

Create a Dropbox API app/token with the least privileges needed to read the designated source folder. The Dropbox token used by ChatGPT's connected app is not automatically available to Codespaces. Do not put real values in `.env.example`; `.gitignore` excludes local `.env` files.

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

A dry run lists supported files and parses/chunks them without writing to Supabase. A normal run writes to the database. First model load downloads model weights, so initial run may take several minutes.

## Important status

This is an integration scaffold, not proof of a successful live ingestion. Configure secrets, apply the SQL migration in `supabase/migrations`, run healthcheck and ingestion, then verify document/chunk counts and a retrieval query. No Dropbox or Supabase credentials are stored in this repository.
