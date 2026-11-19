import subprocess
DEFAULT_ALLOWLIST=("python -m pytest","python -m unittest","ruff check")
def run_allowlisted(command,timeout=30,allowlist=DEFAULT_ALLOWLIST):
 if not any(command==x or command.startswith(x+" ") for x in allowlist): raise PermissionError("command not allowlisted")
 r=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=min(timeout,300),check=False)
 return {"stdout":r.stdout,"stderr":r.stderr,"exit_code":r.returncode,"evidence_tags":[]}
