"""Runtime validation for UGAI task plans."""
from __future__ import annotations
from dataclasses import dataclass
from .mode_router import Mode

class PlanValidationError(ValueError):
    pass

@dataclass(frozen=True)
class PlanStep:
    id: int
    tool: str
    args: dict
    expected_evidence: tuple[str, ...]
    on_failure: str = "abort"

@dataclass(frozen=True)
class TaskPlan:
    mode: Mode
    task: str
    steps: tuple[PlanStep, ...]
    assumptions: tuple[str, ...] = ()
    abort_conditions: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.task.strip():
            raise PlanValidationError("task must not be empty")
        if not self.steps:
            raise PlanValidationError("plan must contain at least one step")
        limit = 20 if self.mode == Mode.PLANNED else 50
        if len(self.steps) > limit:
            raise PlanValidationError(f"{self.mode.value} plan exceeds {limit} steps")
        ids = [step.id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise PlanValidationError("step IDs must be unique")
        for step in self.steps:
            if step.id < 0:
                raise PlanValidationError(f"step {step.id}: id must be non-negative")
            if not isinstance(step.args, dict):
                raise PlanValidationError(f"step {step.id}: args must be an object")
            if not step.tool.strip():
                raise PlanValidationError(f"step {step.id}: tool is required")
            if not step.expected_evidence or any(not tag.strip() for tag in step.expected_evidence):
                raise PlanValidationError(f"step {step.id}: expected_evidence must contain non-empty tags")
            if step.on_failure not in {"abort", "retry_once", "skip"}:
                raise PlanValidationError(f"step {step.id}: invalid on_failure policy")
        if not self.abort_conditions:
            raise PlanValidationError("abort_conditions must be explicit")
