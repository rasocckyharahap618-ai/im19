from ..errors import PlanValidationError
class Planner:
 def validate(self,p):
  limit=20 if p.mode.value=="PLANNED" else 50
  if len(p.steps)>limit: raise PlanValidationError("step limit exceeded")
  ids=[s.id for s in p.steps]
  if len(ids)!=len(set(ids)) or any(i<0 for i in ids): raise PlanValidationError("step IDs must be unique and nonnegative")
  if not p.task.strip() or not p.task_id.strip() or not p.abort_conditions: raise PlanValidationError("task identity and abort conditions required")
  for s in p.steps:
   if not s.tool.strip() or not isinstance(s.args,dict) or not s.expected_evidence or any(not x.strip() for x in s.expected_evidence) or s.on_failure not in {"abort","retry_once","skip"}: raise PlanValidationError(f"invalid step {s.id}")
  return p
