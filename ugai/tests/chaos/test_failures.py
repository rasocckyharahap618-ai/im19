import sqlite3
from core.events.log import EventLog
from core.events.types import EventType
def test_event_sequence_monotonic():
 l=EventLog(sqlite3.connect(":memory:")); assert l.append("r",EventType.RUN_CREATED,{}).sequence==1; assert l.append("r",EventType.STEP_STARTED,{}).sequence==2
