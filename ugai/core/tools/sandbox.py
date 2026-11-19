import subprocess
def run_isolated(argv,cwd,timeout=30,max_output_bytes=1000000,env=None):
 if not argv or not isinstance(argv,list): raise ValueError("argv must be non-empty list")
 r=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=min(timeout,300),env=env,check=False)
 return {"stdout":r.stdout[:max_output_bytes],"stderr":r.stderr[:max_output_bytes],"exit_code":r.returncode}
