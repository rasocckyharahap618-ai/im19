"""Declarative UGAI v3 engineering skill contracts.

These entries define capability metadata only. A skill is executable only
when a host explicitly binds a handler with the documented least-privilege
toolset; no sub-agent runtime is implied.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class SkillSpec:
    skill_id: str
    name: str
    trigger: str
    input_contract: str
    procedure: tuple[str, ...]
    output_contract: str
    failure_mode: str

SKILL_REGISTRY = (
    SkillSpec("S01", "read_and_cite", "Need file content or exact lines", "{path, line_range?}", ("Read the requested path", "Capture exact line range", "Emit doc:path:start-end evidence tag"), "{content, tag}", "Missing path returns unknown; never reconstruct from memory"),
    SkillSpec("S02", "shell_verify", "Need to verify local system state", "{command}", ("Check command against explicit allowlist", "Execute with bounded timeout", "Record stdout, stderr, exit code and cmd tag"), "{stdout, stderr, exit_code, tag}", "Denied command is not retried or bypassed"),
    SkillSpec("S03", "plan_decompose", "PLANNED, ORCHESTRATED, or DYNAMIC mode", "{task, available_tools, constraints}", ("Create bounded ordered steps", "Require expected_evidence per step", "Declare failure policy, assumptions and abort conditions"), "TaskPlan", "Reject any step without expected evidence"),
    SkillSpec("S04", "execute_step", "A validated plan step is ready", "{step}", ("Call only the declared tool and arguments", "Verify expected evidence was emitted", "Emit STEP_COMPLETED or STEP_FAILED"), "{outcome, evidence_tags, output}", "Retry at most once when policy says retry_once"),
    SkillSpec("S05", "spawn_specialist", "ORCHESTRATED mode needs isolated expertise", "{role, subtask, tools, budget_usd}", ("Use approved role and minimal toolset", "Enforce specialist budget and concurrency cap", "Require structured result and evidence tags"), "{specialist_id, result, evidence_tags}", "Unavailable until a real host sub-agent runtime is connected"),
    SkillSpec("S06", "write_orchestration_script", "DYNAMIC mode for repetitive large-scale work", "{task, pattern, file_list}", ("Generate deterministic idempotent script", "Hash the exact script for audit", "Forbid eval, external fetch and writes outside workspace"), "{script_js, script_hash}", "Do not execute without a constrained script runtime"),
    SkillSpec("S07", "verify_claims", "Before finalizing confirmed claims", "{claims, ledger}", ("Require evidence for confirmed claims", "Check doc/cmd tags against ledger", "Downgrade assumptions to probable"), "{verified, rejected, missing}", "Reject or downgrade unsupported claims"),
    SkillSpec("S08", "gate_check", "Before final response", "{task_view, ledger, response}", ("Evaluate G1 numeric provenance", "Evaluate G2 artifacts and G3 execution claims", "Evaluate G4 hedging, G5 falsifiability, G6 scores and G7 coverage"), "{passed, violations}", "Block final response when any gate fails"),
    SkillSpec("S09", "escalate_human", "Sensitive action or high-impact ambiguity", "{question, context, options}", ("Ask one specific decision question", "Present two or three consequences", "Wait for explicit decision"), "{decision, rationale}", "Do not proceed on silent assumptions"),
    SkillSpec("S10", "rollback", "Gate failure after a mutation or execution drift", "{checkpoint_id}", ("Restore the verified checkpoint", "Emit failed state transition", "Stop automatic retries"), "{restored_state}", "If checkpoint is unavailable, stop and report unknown state"),
    SkillSpec("S11", "summarize_evidence", "Context pressure or long evidence trail", "{tag_list}", ("Summarize each selected evidence item", "Preserve original evidence tags", "Keep source records unchanged in ledger"), "{summary, kept_tags}", "Never alter names, values or original citations"),
    SkillSpec("S12", "abort_cleanly", "Abort condition reached or budget exhausted", "{reason, partial_state}", ("Stop in-flight work where supported", "Report completed, failed and pending work", "Emit structured TASK_FAILED event"), "{report}", "Never conceal partial failure or orphaned operations"),
)

SKILLS_BY_ID = {skill.skill_id: skill for skill in SKILL_REGISTRY}
