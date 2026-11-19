# UGAI modular runtime architecture

## Runtime boundaries
- `core/types.py` defines stable task, plan, run, and mode types.
- `core/orchestrator` validates plans, runs registered tools in deterministic order, emits lifecycle events, and applies approval/budget supervision.
- `core/events` stores append-only per-run events in SQLite; projections rebuild run state.
- `core/evidence` persists evidence payloads and provides exact-tag lookup. Presence is provenance, not semantic entailment.
- `core/model` defines provider contracts and optional Anthropic/OpenAI adapters. Credentials and model IDs are read from environment variables only.
- `core/guard` validates JSON Schema, policy and workspace boundaries.
- `api` and `cli` are thin entry points. Task API currently acknowledges but does not dispatch work; no production worker is implied.

## Persistence and deployment
SQLite is the initial local persistence adapter. Event/evidence tables are append-oriented; migrations are explicit. Docker Compose mounts a named volume at `/data`. Use a single-process deployment until a server-grade database and concurrency tests are implemented.

## Safety limits
Shell execution is allowlisted; filesystem tools resolve paths under a workspace root. Mutating tools require explicit approval through the supervisor. Never mount secrets into untrusted tool sandboxes. Provider SDKs are optional dependencies. Do not deploy before CI, security review, auth, worker dispatch, rate limits, and backup/restore validation.

## Deferred production work
Durable approval identities/workflow, background worker/queue, Postgres adapter, atomic lease semantics across processes, provider cost tables and real token pricing, semantic citation verification, OpenTelemetry exporters, Prometheus endpoint, API authentication/authorization, rate limiting, and end-to-end chaos testing.
