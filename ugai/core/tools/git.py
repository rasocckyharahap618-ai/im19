import subprocess
def status(cwd="."):
 r=subprocess.run(["git","status","--short","--branch"],cwd=cwd,capture_output=True,text=True,check=False)
 return {"stdout":r.stdout,"exit_code":r.returncode,"evidence_tags":[]}
