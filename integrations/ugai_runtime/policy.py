"""Pre-action policy decisions for budget and sensitive operations."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class PolicyDecision(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    REQUIRE_HUMAN = "require_human"
    ABORT = "abort"

@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    reason: str

class PolicyEngine:
    SENSITIVE_ACTIONS = frozenset({
        "write_main", "modify_secrets", "modify_ci", "modify_infra",
        "modify_deployment", "modify_supabase", "destructive_migration",
        "publish", "submit_manuscript", "delete_source",
    })

    def evaluate(self, *, action: str, spent_usd: float, budget_usd: float,
                 assumptions_count: int = 0, estimated_cost_usd: float = 0.0) -> PolicyResult:
        if budget_usd <= 0 or spent_usd < 0 or estimated_cost_usd < 0:
            raise ValueError("budget must be positive and costs non-negative")
        if spent_usd > budget_usd:
            return PolicyResult(PolicyDecision.ABORT, "hard budget cap exceeded")
        if action in self.SENSITIVE_ACTIONS:
            return PolicyResult(PolicyDecision.REQUIRE_HUMAN, f"human approval required for {action}")
        if assumptions_count > 3 and estimated_cost_usd > 0.50:
            return PolicyResult(PolicyDecision.REQUIRE_HUMAN, "more than three assumptions and estimated cost exceeds $0.50")
        if spent_usd >= budget_usd * 0.80:
            return PolicyResult(PolicyDecision.WARN, "budget usage is at or above 80%")
        return PolicyResult(PolicyDecision.ALLOW, "within policy")
