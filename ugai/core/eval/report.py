import json
def write_report(results,path="eval-report.json"):
 with open(path,"w",encoding="utf-8") as f: json.dump(results,f,indent=2,sort_keys=True)
 return path
