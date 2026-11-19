import json
class CheckpointStore:
 def __init__(self,db): self.db=db; db.execute("CREATE TABLE IF NOT EXISTS checkpoints(run_id TEXT PRIMARY KEY,sequence INTEGER,state_json TEXT)"); db.commit()
 def save(self,run_id,sequence,state):
  with self.db: self.db.execute("INSERT INTO checkpoints VALUES(?,?,?) ON CONFLICT(run_id) DO UPDATE SET sequence=excluded.sequence,state_json=excluded.state_json",(run_id,sequence,json.dumps(state,sort_keys=True)))
 def load(self,run_id):
  r=self.db.execute("SELECT sequence,state_json FROM checkpoints WHERE run_id=?",(run_id,)).fetchone(); return None if not r else {"sequence":r[0],"state":json.loads(r[1])}
