from pathlib import Path
class Policy:
 def __init__(self,data): self.data=data
 @classmethod
 def load(cls,path="contracts/decision_policy.yaml"):
  import yaml
  return cls(yaml.safe_load(Path(path).read_text()))
 def threshold(self,name): return self.data["thresholds"][name]
