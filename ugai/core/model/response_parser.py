import json
from pydantic import BaseModel,ConfigDict,ValidationError
from ..types import Mode
from ..errors import UGAIError
class Claim(BaseModel): model_config=ConfigDict(extra="allow"); text:str; evidence:str; status:str
class AgentResponse(BaseModel):
 model_config=ConfigDict(extra="allow")
 mode_used:Mode; answer:str; claims:list[Claim]; skills_used:list[str]=[]; unknowns:list[str]=[]; assumptions:list[str]=[]; verification_needed:list[str]=[]; cost_usd:float=0; next_action:str=""
def parse_response(raw):
 try: return AgentResponse.model_validate(json.loads(raw))
 except (ValueError,ValidationError) as e: raise UGAIError(f"invalid response: {e}") from e
