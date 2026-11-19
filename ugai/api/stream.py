import json
def encode_sse(event): return "data: "+json.dumps(event,separators=(",",":"))+"\n\n"
