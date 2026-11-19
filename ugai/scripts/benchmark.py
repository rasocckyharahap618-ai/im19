import time
from core.eval.metrics import aggregate
def main():
 t=time.perf_counter(); results=[{"result":{"passed":True}} for _ in range(10000)]; print({"cases":len(results),"metrics":aggregate(results),"elapsed_seconds":time.perf_counter()-t})
if __name__=="__main__":main()
