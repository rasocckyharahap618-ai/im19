from ..events.types import EventType
from ..errors import EvidenceMissing,ToolExecutionError
class PlanExecutor:
 def __init__(self,log,tools): self.log=log; self.tools=tools
 def execute(self,plan):
  out=[]
  for step in plan.steps:
   fn=self.tools.get(step.tool)
   if fn is None: raise ToolExecutionError(f"unknown tool: {step.tool}")
   self.log.append(plan.task_id,EventType.STEP_STARTED,{"step_id":step.id})
   for attempt in range(2 if step.on_failure=="retry_once" else 1):
    try:
     result=fn(**step.args); tags=set(result.get("evidence_tags",[])); missing=set(step.expected_evidence)-tags
     if missing: raise EvidenceMissing(str(sorted(missing)))
     self.log.append(plan.task_id,EventType.STEP_COMPLETED,{"step_id":step.id,"evidence_tags":sorted(tags)}); out.append(result); break
    except Exception as e:
     if attempt+1==(2 if step.on_failure=="retry_once" else 1):
      self.log.append(plan.task_id,EventType.STEP_FAILED,{"step_id":step.id,"error":type(e).__name__})
      if step.on_failure!="skip": raise
      out.append({"skipped":True})
  return out
