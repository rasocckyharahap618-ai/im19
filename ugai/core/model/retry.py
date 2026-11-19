import random,time
def retry(operation,attempts=2,base_delay=.25,max_delay=4,retry_if=lambda e:True):
 for i in range(attempts):
  try: return operation()
  except Exception as e:
   if i+1>=attempts or not retry_if(e): raise
   time.sleep(min(max_delay,base_delay*2**i)*random.uniform(.7,1.3))
