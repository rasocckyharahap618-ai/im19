# UGAI Research Agent — Foundation Architecture

## Purpose
This change adds an isolated, standard-library-only research-agent foundation
inside IM 19. It does not replace or modify the existing Dropbox → Supabase
RAG integration.

## Components
- Contracts: immutable task, plan, event records, and run status.
- Orchestrator: deterministic sequential execution through injected handlers.
- Research skills: declarative catalogue of 20 domain capabilities.
- Evidence Ledger: append-only in-memory source records with provenance and
  SHA-256 digest of any stored excerpt.
- Evidence Guard: verifies that citation markers resolve to ledger records.
  It does not prove that a source substantively supports a claim.

## Execution flow
1. Host creates an AgentPlan with one or more AgentTask entries.
2. Host registers a handler for each task skill.
3. Orchestrator emits lifecycle events and executes tasks in order.
4. Results and failures are captured in an AgentRun.
5. Host validates evidence markers before returning a cited answer.

## Evidence marker convention
Use [EV-<stable-id>] in research text. Each marker must resolve to an
EvidenceRecord. Store source name, title, canonical locator, optional DOI,
publication date, retrieval timestamp, and excerpt. The digest is integrity
metadata, not proof of source validity.

## Safety boundaries
- Never fabricate references, DOIs, quotations, statistics, or study results.
- Verify journal indexing and quartile claims against authoritative current
  sources before presenting them as facts.
- A valid evidence ID is not equivalent to claim-level entailment. Human
  critical appraisal remains necessary.
- Manuscript submission, publication, source deletion, and other irreversible
  external actions require explicit human approval.
- No credentials, database access, external API calls, deployment, or CI
  changes are introduced by this foundation.

## Run tests
From the repository root:
```bash
python -m unittest tests.test_research_agent_core -v
python -m unittest discover -s tests -v
```

## Deferred work
1. Persistent event/evidence storage behind repository interfaces.
2. Model-provider adapters with structured output validation.
3. Search connectors (Crossref, OpenAlex, PubMed, Semantic Scholar, DOAJ,
   SINTA, Scopus, and Web of Science), subject to source licensing.
4. API/CLI, authentication, authorization, observability, and evaluation.
5. Integration with existing RAG only through a separately reviewed adapter.

No provider connector is considered available merely because it is listed.
Production use requires threat modelling, access-control review, integration
tests, human review, and an approved rollout.
