# IM 19 Institutional RAG Mining — operational standard

## Scope

This layer adds deterministic text normalization, document quality gates, content hashes, chunk provenance, and offline retrieval metrics to the existing Dropbox → Supabase pgvector RAG. It intentionally reuses the current institutional schema and RPC contract. It does not create new database tables or run migrations.

## Mining pipeline

1. Discover files only under the configured Dropbox source folder; do not crawl the entire account.
2. Validate supported extensions and size before extraction.
3. Extract text from TXT, Markdown, HTML, PDF, and DOCX using the existing ingestion module.
4. Normalize Unicode and whitespace without rewriting meaning.
5. Apply a quality gate to reject empty, too-short, oversized, or likely corrupted extraction output.
6. Fingerprint normalized content with SHA-256 for change detection and provenance.
7. Chunk deterministically with overlap. The helper uses character lengths, not model-token counts.
8. Embed with the configured 384-dimensional model and validate vector dimensions and finite values.
9. Persist only after checking the target project's actual schema and migration history.
10. Retrieve through the existing match_rag_chunks RPC and return source metadata for citations.
11. Evaluate with a human-reviewed JSONL test set; measure source hit rate, MRR, precision@k, and recall@k.
12. Preserve source version, content hash, pipeline version, timestamps, and ingestion outcomes in an approved audit store.

## Run offline checks

    python -m compileall -q integrations/rag scripts tests
    python -m unittest discover -s tests -v
    python scripts/rag_preflight.py

## Evaluate saved retrieval results

Each JSONL line contains a case object and a results list. Example:

    {"case":{"id":"q1","query":"What is the policy?","relevant_source_uris":["dropbox:///policy.md"]},"results":[{"source_uri":"dropbox:///policy.md","content":"Policy text..."}]}

Run:

    python scripts/rag_evaluate_jsonl.py --input tests/fixtures/rag_eval_results.jsonl --k 5

Evaluation numbers are meaningful only when cases and retrieved results came from the intended corpus and were reviewed. The sample fixture is only a format example and is not a production quality claim.

## Production-readiness gates

- Verify Dropbox token scope and folder path; never ingest the entire account.
- Verify the target Supabase project and migration history before applying SQL.
- Resolve atomicity between document metadata upsert and chunk replacement before live ingestion.
- Add identity-bound authorization before serving multiple users or tenants. Metadata filters alone are not access control.
- Keep the service-role key server-side only. Never expose it to browser code, MCP tool output, logs, or prompts.
- Add retries/backoff, bounded concurrency, ingestion checkpointing, and dead-letter handling before large-scale corpus mining.
- Treat retrieved documents as untrusted data, not instructions to privileged agents.
- Review copyright, licensing, retention, and source permissions for each corpus.
- Use a reviewed pull request and staging corpus before production ingestion.
