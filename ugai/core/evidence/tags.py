import re
PATTERN=re.compile(r"^(doc:.+:\d+-\d+|cmd:[A-Za-z0-9_-]+|api:[A-Za-z0-9_-]+:[A-Za-z0-9_-]+|event:.+:\d+|\[assume\]|\[unknown\])$")
def valid_tag(tag): return bool(PATTERN.match(tag))
