from enum import StrEnum
from ..errors import UGAIError
class CircuitState(StrEnum): CLOSED="closed"; OPEN="open"; HALF_OPEN="half_open"
class CircuitBreaker:
 def __init__(self,threshold=5): self.threshold=threshold; self.failures=0; self.state=CircuitState.CLOSED
 def allow(self):
  if self.state==CircuitState.OPEN: raise UGAIError("circuit open")
  if self.state==CircuitState.HALF_OPEN: self.state=CircuitState.CLOSED
 def success(self): self.failures=0; self.state=CircuitState.CLOSED
 def failure(self):
  self.failures+=1
  if self.failures>=self.threshold: self.state=CircuitState.OPEN
