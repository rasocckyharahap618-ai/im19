from core.events.projection import project
def replay(run_id,event_log): return project(run_id,event_log.read(run_id))
