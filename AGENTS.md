# AGENTS — Shared Agent Rules for rasocckyharahap618-ai/im19

This file defines repository conventions and non-conflicting agent rules for OpenCode and GitHub Copilot. These are human-reviewed, repository-level instructions that all automated agents must follow before making changes.

Principles
- Always plan before implementing. Agents MUST produce a short Implementation Plan (1–3 steps) and wait for human approval when the change touches security-sensitive areas (secrets, CI, infra, deployment, or Supabase configuration).
- Prefer documentation and small, reviewable patches. Large or risky changes must be split into multiple PRs with tests and architecture notes.
- Never deploy or enable production workflows without an explicit signed approval from the repository owner.

Repository conventions
- Keep the repo language-agnostic unless the repository already contains a manifest (package.json, pyproject.toml, go.mod, Cargo.toml, etc.).
- Directory layout (preferred minimum):
  - src/         Source code (language-specific layout inside)
  - tests/       Tests organized as tests/unit and tests/integration
  - config/      Configuration templates and validation helpers
  - scripts/     Developer scripts (lint, test wrappers, local dev helpers)
  - docs/        Architecture and operational documentation
- Follow conventional commit messages and include a concise changelog entry for breaking changes.

Planning before implementation
- Every agent-originated change must include in the PR description:
  1. A short implementation plan (3–5 bullet points).
  2. The files affected and why.
  3. A test plan and rollout plan (how to verify and how to revert).
- If an agent cannot write a meaningful test for its change, it must not merge the change without human approval.

Tests and code review
- Unit tests are required for all new business logic. Integration tests are required for any code that interacts with external services (Supabase, Binance API).
- Tests must run locally and in CI. CI must fail on test failures.
- Pull requests require at least one human code reviewer before merging. Automated approvals from agents are informational only.

Supabase security requirements (summary)
- Never store service_role or other “admin” keys in the repository. These keys must only exist in secure CI secrets or a protected environment.
- RLS (Row-Level Security) must be enabled for all production and staging databases by default; migrations must include RLS policy templates for review.
- Keep remote database operations disabled by default in development scripts; connect only when a development Supabase project exists and is explicitly configured.

Secret-handling rules
- Secrets must be provided through environment variables or CI secret stores; never commit credentials to git.
- Use a secret-scanning tool in CI (e.g., git-secrets, truffleHog, or GitHub Advanced Security secret scanning) and fail the build if secrets are detected.
- Enforce minimal scope for keys and rotate regularly.

Prohibitions and safeguards
- No production deployment or execution of trading orders without explicit human authorization and documented approvals.
- Agents may prepare release artifacts, but only humans may release or deploy to production.
- Automated code that would perform financial transactions (placing orders, moving funds) is strictly prohibited until reviewed and enabled by a named human owner.

How to use these rules (for agents and humans)
1. Read this file before proposing changes that affect CI, secrets, deployment, or database access.
2. When proposing code changes, include a short plan and test plan in the PR body.
3. Tag a human reviewer for approval on security-sensitive changes.

Appendix: Example PR template checklist (to be added to .github when PR templates are introduced)
- [ ] Implementation plan included
- [ ] Tests added and passing
- [ ] Secrets not committed
- [ ] Supabase changes reviewed (if any)
- [ ] Human reviewer assigned for security-sensitive changes
