def aggregate(results):
 total=len(results); passed=sum(bool(x.get("result",{}).get("passed")) for x in results)
 return {"total":total,"passed":passed,"failed":total-passed,"pass_rate":passed/total if total else 0.0}
