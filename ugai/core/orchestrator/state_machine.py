from ..types import RunStatus
from ..events.types import EventType
from ..errors import InvalidTransition
ALLOWED={RunStatus.PENDING:{RunStatus.PLANNING,RunStatus.CANCELLED},RunStatus.PLANNING:{RunStatus.RUNNING,RunStatus.WAITING_APPROVAL,RunStatus.FAILED},RunStatus.RUNNING:{RunStatus.WAITING_APPROVAL,RunStatus.COMPLETED,RunStatus.FAILED,RunStatus.CANCELLED},RunStatus.WAITING_APPROVAL:{RunStatus.RUNNING,RunStatus.CANCELLED,RunStatus.FAILED},RunStatus.COMPLETED:set(),RunStatus.FAILED:set(),RunStatus.CANCELLED:set()}
class StateMachine:
 def __init__(self,log): self.log=log
 def transition(self,run_id,current,target,reason=""):
  if target not in ALLOWED[current]: raise InvalidTransition(f"{current}->{target}")
  return self.log.append(run_id,EventType.STATE_TRANSITION,{"from":current.value,"to":target.value,"reason":reason})
