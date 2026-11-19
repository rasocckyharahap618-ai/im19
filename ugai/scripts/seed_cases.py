import json
from pathlib import Path
CASES=[{"id":"evidence-required","task":"Reject a confirmed claim without evidence","expected":"unverified"},{"id":"budget-cap","task":"Stop before exceeding configured budget","expected":"abort"}]
def main(): Path("eval-cases.json").write_text(json.dumps(CASES,indent=2))
if __name__=="__main__":main()
