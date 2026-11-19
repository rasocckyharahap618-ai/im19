import json,logging
logger=logging.getLogger("ugai.audit")
def audit(action,actor,resource,metadata=None): logger.info(json.dumps({"action":action,"actor":actor,"resource":resource,"metadata":metadata or {}},sort_keys=True))
