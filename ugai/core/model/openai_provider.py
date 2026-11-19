from .base import ModelResponse
from ..errors import ConfigurationError,ProviderError
class OpenAIProvider:
 def __init__(self,api_key,model):
  if not api_key or not model: raise ConfigurationError("OPENAI_API_KEY and OPENAI_MODEL required")
  try: from openai import OpenAI
  except ImportError as e: raise ConfigurationError("install ugai[openai]") from e
  self.client=OpenAI(api_key=api_key); self.model=model
 def generate(self,system,prompt,max_tokens=4096):
  try:
   r=self.client.chat.completions.create(model=self.model,max_tokens=max_tokens,messages=[{"role":"system","content":system},{"role":"user","content":prompt}]); u=r.usage
   return ModelResponse(r.choices[0].message.content or "",u.prompt_tokens,u.completion_tokens,self.model,r.id)
  except Exception as e: raise ProviderError(str(e)) from e
