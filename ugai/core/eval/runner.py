class EvalRunner:
 def __init__(self,cases,evaluator): self.cases=cases; self.evaluator=evaluator
 def run(self): return [{"case_id":c["id"],"result":self.evaluator(c)} for c in self.cases]
