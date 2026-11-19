from ..errors import BudgetExceeded,PolicyDenied
class Supervisor:
 def __init__(self,policy): self.policy=policy
 def check_budget(self,spent,cap):
  ratio=spent/cap
  if ratio>=self.policy["thresholds"]["budget_hard_limit_ratio"]: raise BudgetExceeded("hard budget cap reached")
  return "warning" if ratio>=self.policy["thresholds"]["budget_warning_ratio"] else "ok"
 def authorize(self,tool,effects,approved=False):
  if set(effects)&{"write","execute","external","irreversible"} and not approved: raise PolicyDenied(f"approval required: {tool}")
