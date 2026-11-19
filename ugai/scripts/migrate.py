import sqlite3
from pathlib import Path
def main():
 db=sqlite3.connect("ugai.db")
 for p in sorted(Path("core/db/migrations").glob("*.sql")): db.executescript(p.read_text())
 db.commit(); db.close()
if __name__=="__main__":main()
