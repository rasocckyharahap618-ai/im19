from ..errors import EvidenceMissing
class EvidenceVerifier:
 def __init__(self,ledger): self.ledger=ledger
 def verify_tags(self,tags):
  missing=[x for x in tags if not self.ledger.contains(x)]
  if missing: raise EvidenceMissing(", ".join(missing))
  return True
