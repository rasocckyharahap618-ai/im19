class ToolRegistry:
 def __init__(self): self._tools={}
 def register(self,spec):
  if spec.name in self._tools: raise ValueError("duplicate tool")
  self._tools[spec.name]=spec
 def get(self,name): return self._tools[name]
 def handlers(self): return {k:v.handler for k,v in self._tools.items()}
