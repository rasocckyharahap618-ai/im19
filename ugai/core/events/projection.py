from .types import Event
from ..types import RunState,RunStatus
def project(run_id,events):
 s=RunState(run_id)
 for e in events:
  s.last_sequence=e.sequence
  if e.event_type.value=="STATE_TRANSITION": s.status=RunStatus(e.payload["to"])
  elif e.event_type.value=="STEP_COMPLETED": s.completed_steps.append(int(e.payload["step_id"]))
  elif e.event_type.value=="STEP_FAILED": s.failed_steps.append(int(e.payload["step_id"]))
  elif e.event_type.value=="BUDGET_CHARGED": s.budget_spent_usd+=float(e.payload["amount_usd"])
  elif e.event_type.value=="TASK_FAILED": s.status=RunStatus.FAILED
 return s
