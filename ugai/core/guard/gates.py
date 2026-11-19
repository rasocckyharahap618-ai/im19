from dataclasses import dataclass
@dataclass(frozen=True)
class GateResult: passed:bool; violations:tuple[str,...]
class QualityGates:
 def check(self,task,response,ledger):
  v=[]; claims=response.get("claims",[]); answer=response.get("answer","")
  if any(c.get("status")=="confirmed" and (not c.get("evidence") or c["evidence"] not in ledger) for c in claims): v.append("G1/G2 unsupported confirmed claim")
  if any(x in answer.lower() for x in ("tested","test passed","lulus")) and not any(c.get("execution_evidence") for c in claims): v.append("G3 execution claim lacks evidence")
  if response.get("recommendations") and not response.get("falsification_conditions"): v.append("G5 recommendation lacks falsification condition")
  missing=set(task.get("required_sections",[]))-set(response.get("covered_sections",[]))
  if missing: v.append("G7 missing sections: "+", ".join(sorted(missing)))
  return GateResult(not v,tuple(v))
