import json, sqlite3
from datetime import datetime, timezone
from .types import Event, EventType

class EventLog:
    def __init__(self, connection: sqlite3.Connection):
        self.db=connection
        self.db.execute("""CREATE TABLE IF NOT EXISTS events(run_id TEXT NOT NULL, sequence INTEGER NOT NULL, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(run_id,sequence))""")
        self.db.commit()
    def append(self, run_id: str, event_type: EventType, payload: dict) -> Event:
        with self.db:
            row=self.db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM events WHERE run_id=?",(run_id,)).fetchone()
            seq=int(row[0]); stamp=datetime.now(timezone.utc).isoformat()
            self.db.execute("INSERT INTO events VALUES(?,?,?,?,?)",(run_id,seq,event_type.value,json.dumps(payload,sort_keys=True),stamp))
        return Event(run_id,seq,event_type,payload,stamp)
    def read(self, run_id: str, after: int=0) -> list[Event]:
        rows=self.db.execute("SELECT run_id,sequence,event_type,payload,created_at FROM events WHERE run_id=? AND sequence>? ORDER BY sequence",(run_id,after)).fetchall()
        return [Event(r[0],r[1],EventType(r[2]),json.loads(r[3]),r[4]) for r in rows]
