import sqlite3
from pathlib import Path
class Store:
 def __init__(self,url):
  if not url.startswith("sqlite:///"): raise ValueError("only sqlite:/// is supported by initial store")
  path=url.removeprefix("sqlite:///")
  if path!=":memory:": Path(path).parent.mkdir(parents=True,exist_ok=True)
  self.connection=sqlite3.connect(path,check_same_thread=False); self.connection.row_factory=sqlite3.Row
 def close(self): self.connection.close()
