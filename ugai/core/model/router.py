from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate: name:str; provider:object; input_cost:float; output_cost:float; latency_ms:int
class ModelRouter:
 def __init__(self,candidates): self.candidates=candidates
 def select(self,strategy="balanced"):
  if not self.candidates: raise ValueError("no providers configured")
  key={"cost":lambda x:x.input_cost+x.output_cost,"latency":lambda x:x.latency_ms,"balanced":lambda x:x.latency_ms/1000+x.input_cost+x.output_cost}[strategy]
  return min(self.candidates,key=key)
