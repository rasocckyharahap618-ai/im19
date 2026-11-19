from dataclasses import dataclass
import os
@dataclass(frozen=True)
class Settings:
    environment:str="development"; database_url:str="sqlite:///./ugai.db"; budget_default_usd:float=2.0; max_context_tokens:int=200000; log_level:str="INFO"; anthropic_model:str|None=None; openai_model:str|None=None
    @classmethod
    def from_env(cls):
        budget=float(os.getenv("UGAI_BUDGET_DEFAULT_USD","2"))
        if budget<=0: raise ValueError("budget must be positive")
        return cls(os.getenv("UGAI_ENV","development"),os.getenv("UGAI_DATABASE_URL","sqlite:///./ugai.db"),budget,int(os.getenv("UGAI_MAX_CONTEXT_TOKENS","200000")),os.getenv("UGAI_LOG_LEVEL","INFO"),os.getenv("ANTHROPIC_MODEL"),os.getenv("OPENAI_MODEL"))
