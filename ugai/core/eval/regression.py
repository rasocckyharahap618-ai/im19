def compare(baseline,current,threshold=0):
 delta=current.get("pass_rate",0)-baseline.get("pass_rate",0)
 return {"delta":delta,"regression":delta < -threshold}
