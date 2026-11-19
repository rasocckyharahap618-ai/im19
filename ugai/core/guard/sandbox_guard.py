from pathlib import Path
class SandboxGuard:
 def __init__(self,root): self.root=Path(root).resolve()
 def resolve(self,path):
  p=(self.root/path).resolve()
  if p!=self.root and self.root not in p.parents: raise PermissionError("path escapes workspace")
  return p
