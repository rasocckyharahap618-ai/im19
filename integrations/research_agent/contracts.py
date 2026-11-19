"""Typed contracts shared by the UGAI research runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RunStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass(frozen=True)
class AgentTask:
    task_id: str
    description: str
    skill: str
    input: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class AgentPlan:
    run_id: str
    objective: str
    tasks: tuple[AgentTask, ...]
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, objective: str, tasks: list[AgentTask]) -> "AgentPlan":
        if not objective.strip():
            raise ValueError("objective must not be empty")
        if not tasks:
            raise ValueError("plan must contain at least one task")
        return cls(run_id=str(uuid4()), objective=objective, tasks=tuple(tasks))

@dataclass(frozen=True)
class AgentEvent:
    run_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utc_now)

@dataclass
class AgentRun:
    plan: AgentPlan
    status: RunStatus = RunStatus.PLANNED
    outputs: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
