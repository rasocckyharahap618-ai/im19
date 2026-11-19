import sqlite3,pytest
from core.events.log import EventLog
from core.events.types import EventType
from core.events.projection import project
from core.types import RunStatus,TaskPlan,PlanStep,Mode
from core.orchestrator.planner import Planner
from core.orchestrator.state_machine import StateMachine
from core.orchestrator.checkpoint import CheckpointStore
from core.evidence.ledger import EvidenceLedger
from core.model.budget import Budget
from core.errors import BudgetExceeded,InvalidTransition
def test_event_projection():
 db=sqlite3.connect(":memory:"); log=EventLog(db); log.append("r",EventType.STATE_TRANSITION,{"to":"RUNNING"}); log.append("r",EventType.STEP_COMPLETED,{"step_id":1}); s=project("r",log.read("r")); assert s.status==RunStatus.RUNNING and s.completed_steps==[1]
def test_transition_terminal_rejected():
 with pytest.raises(InvalidTransition): StateMachine(EventLog(sqlite3.connect(":memory:"))).transition("r",RunStatus.COMPLETED,RunStatus.RUNNING)
def test_plan_validation():
 p=TaskPlan("r",Mode.PLANNED,"task",(PlanStep(0,"tool",{},("doc:a:1-2",)),),abort_conditions=("stop",)); assert Planner().validate(p)==p
 with pytest.raises(Exception): Planner().validate(TaskPlan("r",Mode.PLANNED,"task",(PlanStep(0,"tool",{},()),),abort_conditions=("stop",)))
def test_ledger_checkpoint_and_budget():
 db=sqlite3.connect(":memory:"); l=EvidenceLedger(db); l.add("doc:a:1-2","doc","text"); assert l.contains("doc:a:1-2"); c=CheckpointStore(db); c.save("r",3,{"a":1}); assert c.load("r")["sequence"]==3
 b=Budget(1); b.charge(.5)
 with pytest.raises(BudgetExceeded): b.charge(.6)
