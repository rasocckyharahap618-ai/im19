def create_metrics():
 try:
  from prometheus_client import Counter,Histogram
  return {"runs":Counter("ugai_runs_total","UGAI runs"),"duration":Histogram("ugai_run_seconds","UGAI run duration")}
 except ImportError:return {}
