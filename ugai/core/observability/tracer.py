def get_tracer(name="ugai"):
 try:
  from opentelemetry import trace
  return trace.get_tracer(name)
 except ImportError:return None
