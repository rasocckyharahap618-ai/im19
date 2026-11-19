# UGAI-Agent-v3 — Repository Audit and Improvement

## Scope and evidence

This audit compares the supplied v3 operating specification with the repository
state on `feat/ugai-research-agent-foundation`. The repository README says
IM 19 is an Institutional RAG foundation and explicitly states that an
application-runtime orchestrator is not yet implemented or proven. The
Research Agent package on that branch is an initial scaffold, not a complete
v3 runtime.

## Findings before this change

| Area | Existing state | Assessment |
|---|---|---|
| Mode router | No FAST/PLANNED/ORCHESTRATED/DYNAMIC router | Missing |
| Plan contract | AgentPlan only contains objective and tasks | No expected-evidence, step-limit, or failure-policy enforcement |
| Model configuration | No runtime config loader | Cannot enforce env-only model selection |
| Budget policy | No budget accounting or thresholds | Missing |
| Human approval | Helper blocks a few named actions but is not a central policy | Incomplete |
| Claim verification | Citation marker check only | No doc/cmd ledger verification or status downgrade |
| Quality gates | No G1–G7 response gate | Missing |
| Response contract | No machine-readable task-plan or response schema | Missing |
| Specialist execution | No spawnAgent runtime or independent specialist isolation | Not implemented |
| Evidence persistence | In-memory ledger only | Prototype limitation |

## Improvements in this increment

1. Added JSON Schema contracts for task plans and final responses.
2. Added deterministic mode routing implementing the stated file-count and
   specialist-selection rules.
3. Added runtime configuration that fails closed if `ANTHROPIC_MODEL` is
   absent; no model identifier is hard-coded.
4. Added plan validation for unique step IDs, required evidence tags,
   mode-specific step ceilings, failure policy, and abort conditions.
5. Added budget and sensitive-action policy decisions, including human
   approval gates.
6. Added claim evidence verification, assumption downgrading, and G1–G7
   response gate checks.
7. Added unit tests for the new control-plane primitives.

## Important limitations

- JSON Schemas are contract artifacts; this increment does not add a JSON
  Schema validation dependency or claim arbitrary payloads are runtime-
  validated against the schema.
- Budget policy evaluates supplied spend/estimate values; it does not measure
  provider token usage or actual billed cost.
- Evidence verification checks tag presence in a caller-supplied ledger; it
  does not prove that a cited source entails a claim.
- G1–G7 are conservative heuristics and require tuning against an evaluation
  set before production enforcement.
- No spawnAgent/sub-agent runtime exists in this repository. Specialist
  orchestration is documented as unavailable, not simulated.
- Evidence/event persistence, API/CLI, model-provider calls, scholarly search
  connectors, authentication, authorization, and production observability
  remain future work.

## Verification plan

Run from repository root:

```bash
python -m unittest tests.test_ugai_runtime -v
python -m unittest discover -s tests -v
```

Review schema compatibility and false-positive rates for G1–G7 before
connecting these checks to a production response path.

## Safety and rollout

This patch is isolated from `integrations/rag/`, Supabase migrations,
secrets, CI, and deployment. It is a draft, incremental PR against the UGAI
foundation branch. Merge only after human review and test execution.
