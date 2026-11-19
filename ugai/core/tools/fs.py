from pathlib import Path
def _path(path,root):
 base=Path(root).resolve(); target=(base/path).resolve()
 if target!=base and base not in target.parents: raise PermissionError("outside workspace")
 return target
def read_text(path,root="."):
 p=_path(path,root); return {"content":p.read_text(encoding="utf-8"),"evidence_tags":[]}
def write_text(path,content,root="."):
 p=_path(path,root); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8"); return {"path":str(p),"evidence_tags":[]}
