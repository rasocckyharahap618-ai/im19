from .tags import valid_tag
class EvidenceCollector:
 def __init__(self,ledger): self.ledger=ledger
 def record(self,tag,kind,content,metadata=None):
  if not valid_tag(tag): raise ValueError("invalid evidence tag")
  return self.ledger.add(tag,kind,content,metadata or {})
