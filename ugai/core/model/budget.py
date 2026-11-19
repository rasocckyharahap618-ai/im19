from ..errors import BudgetExceeded
class Budget:
 def __init__(self,cap_usd):
  if cap_usd<=0: raise ValueError("cap must be positive")
  self.cap=cap_usd; self.spent=0.0
 def charge(self,amount):
  if amount<0: raise ValueError("negative charge")
  if self.spent+amount>self.cap: raise BudgetExceeded("hard cap")
  self.spent+=amount
 @property
 def remaining(self): return self.cap-self.spent
