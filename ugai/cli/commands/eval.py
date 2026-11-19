from core.eval.runner import EvalRunner
from core.eval.metrics import aggregate
def evaluate(cases,evaluator): return aggregate(EvalRunner(cases,evaluator).run())
