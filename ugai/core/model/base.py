from dataclasses import dataclass
from typing import Protocol
@dataclass(frozen=True)
class ModelResponse: text:str; input_tokens:int; output_tokens:int; model:str; request_id:str|None=None
class ModelProvider(Protocol):
 def generate(self,system:str,prompt:str,max_tokens:int=4096)->ModelResponse: ...
