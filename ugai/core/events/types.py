from dataclasses import dataclass
from enum import StrEnum
from typing import Any
class EventType(StrEnum):
    RUN_CREATED="RUN_CREATED"; STATE_TRANSITION="STATE_TRANSITION"; STEP_STARTED="STEP_STARTED"; STEP_COMPLETED="STEP_COMPLETED"; STEP_FAILED="STEP_FAILED"; APPROVAL_REQUESTED="APPROVAL_REQUESTED"; APPROVAL_GRANTED="APPROVAL_GRANTED"; BUDGET_CHARGED="BUDGET_CHARGED"; TASK_FAILED="TASK_FAILED"
@dataclass(frozen=True)
class Event:
    run_id: str
    sequence: int
    event_type: EventType
    payload: dict[str, Any]
    created_at: str
