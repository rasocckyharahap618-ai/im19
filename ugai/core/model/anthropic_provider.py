from .base import ModelResponse
from ..errors import ConfigurationError,ProviderError
class AnthropicProvider:
 def __init__(self,api_key,model):
  if not api_key or not model: raise ConfigurationError("ANTHROPIC_API_KEY and ANTHROPIC_MODEL required")
  try: from anthropic import Anthropic
  except ImportError as e: raise ConfigurationError("install ugai[anthropic]") from e
  self.client=Anthropic(api_key=api_key); self.model=model
 def generate(self,system,prompt,max_tokens=4096):
  try:
   r=self.client.messages.create(model=self.model,max_tokens=max_tokens,system=system,messages=[{"role":"user","content":prompt}]); text="\n".join(x.text for x in r.content if getattr(x,"type",None)=="text")
   return ModelResponse(text,r.usage.input_tokens,r.usage.output_tokens,self.model,getattr(r,"id",None))
  except Exception as e: raise ProviderError(str(e)) from e
