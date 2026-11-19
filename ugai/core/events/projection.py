from .types import Event
from ..types import RunState, RunStatus

def project(run_id: str, events: list[Event]) -> RunState:
    state=RunState(run_id)
    for event in events:
        state.last_sequence=event.sequence
        if event.event_type.value=="STATE_TRANSITION":
            state.status=RunStatus(event.payload["to"])
        elif event.event_type.value=="STEP_COMPLETED":
            state.completed_steps.append(int(event.payload["step_id"]))
        elif event.event_type.value=="STEP_FAILED":
            state.failed_steps.append(int(event.payload["step_id"]))
        elif event.event_type.value=="BUDGET_CHARGED":
            state.budget_spent_usd+=float(event.payload["amount_usd"])
        elif event.event_type.value=="TASK_FAILED":
            state.status=RunStatus.FAILED
    return state
