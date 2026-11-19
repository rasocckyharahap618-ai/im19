import json
from pathlib import Path
from ..errors import PlanValidationError
def validate_json_schema(instance,schema_path):
 try: from jsonschema import Draft202012Validator
 except ImportError as e: raise RuntimeError("install ugai[dev]") from e
 schema=json.loads(Path(schema_path).read_text()); errors=list(Draft202012Validator(schema).iter_errors(instance))
 if errors: raise PlanValidationError("; ".join(x.message for x in errors))
