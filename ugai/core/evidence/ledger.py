import json
from datetime import datetime,timezone
class EvidenceLedger:
 def __init__(self,db): self.db=db; db.execute("CREATE TABLE IF NOT EXISTS evidence(tag TEXT PRIMARY KEY,kind TEXT,content TEXT,metadata TEXT,created_at TEXT)"); db.commit()
 def add(self,tag,kind,content,metadata=None):
  with self.db: self.db.execute("INSERT INTO evidence VALUES(?,?,?,?,?)",(tag,kind,content,json.dumps(metadata or {},sort_keys=True),datetime.now(timezone.utc).isoformat()))
  return tag
 def get(self,tag):
  r=self.db.execute("SELECT tag,kind,content,metadata,created_at FROM evidence WHERE tag=?",(tag,)).fetchone()
  return None if not r else {"tag":r[0],"kind":r[1],"content":r[2],"metadata":json.loads(r[3]),"created_at":r[4]}
 def contains(self,tag): return self.get(tag) is not None
 def search(self,q,limit=50):
  rows=self.db.execute("SELECT tag,kind,content,metadata,created_at FROM evidence WHERE content LIKE ? LIMIT ?",(f"%{q}%",limit)).fetchall()
  return [{"tag":r[0],"kind":r[1],"content":r[2],"metadata":json.loads(r[3]),"created_at":r[4]} for r in rows]
