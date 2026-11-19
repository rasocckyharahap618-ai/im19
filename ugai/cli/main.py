import argparse
def main():
 p=argparse.ArgumentParser(prog="ugai"); s=p.add_subparsers(dest="command",required=True); r=s.add_parser("run"); r.add_argument("task"); a=p.parse_args()
 if a.command=="run": print({"accepted":True,"task":a.task,"execution":"not_configured"})
if __name__=="__main__":main()
