from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

class Mode(StrEnum):
    FAST="FAST"; PLANNED="PLANNED"; ORCHESTRATED="ORCHESTRATED"; DYNAMIC="DYNAMIC"
class RunStatus(StrEnum):
    PENDING="PENDING"; PLANNING="PLANNING"; RUNNING="RUNNING"; WAITING_APPROVAL="WAITING_APPROVAL"; COMPLETED="COMPLETED"; FAILED="FAILED"; CANCELLED="CANCELLED"
@dataclass(frozen=True)
class PlanStep:
    id: int
    tool: str
    args: dict[str, Any]
    expected_evidence: tuple[str, ...]
    on_failure: str = "abort"
@dataclass(frozen=True)
class TaskPlan:
    task_id: str
    mode: Mode
    task: str
    steps: tuple[PlanStep, ...]
    assumptions: tuple[str, ...] = ()
    abort_conditions: tuple[str, ...] = ()
@dataclass
class RunState:
    run_id: str
    status: RunStatus = RunStatus.PENDING
    completed_steps: list[int] = field(default_factory=list)
    failed_steps: list[int] = field(default_factory=list)
    budget_spent_usd: float = 0.0
    last_sequence: int = 0
