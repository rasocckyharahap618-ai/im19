import time
from ..errors import LeaseConflict
class LeaseStore:
 def __init__(self,db): self.db=db; db.execute("CREATE TABLE IF NOT EXISTS leases(resource TEXT PRIMARY KEY,owner TEXT,expires_at REAL)"); db.commit()
 def acquire(self,resource,owner,ttl=60):
  now=time.time()
  with self.db:
   row=self.db.execute("SELECT owner,expires_at FROM leases WHERE resource=?",(resource,)).fetchone()
   if row and row[1]>now and row[0]!=owner: raise LeaseConflict(resource)
   self.db.execute("INSERT INTO leases VALUES(?,?,?) ON CONFLICT(resource) DO UPDATE SET owner=excluded.owner,expires_at=excluded.expires_at",(resource,owner,now+ttl))
 def release(self,resource,owner):
  with self.db: self.db.execute("DELETE FROM leases WHERE resource=? AND owner=?",(resource,owner))
