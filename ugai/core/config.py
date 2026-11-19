from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    database_url: str = "sqlite:///./ugai.db"
    budget_default_usd: float = 2.0
    max_context_tokens: int = 200_000
    log_level: str = "INFO"
    anthropic_model: str | None = None
    openai_model: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        budget = float(os.getenv("UGAI_BUDGET_DEFAULT_USD", "2.00"))
        if budget <= 0:
            raise ValueError("UGAI_BUDGET_DEFAULT_USD must be positive")
        return cls(
            environment=os.getenv("UGAI_ENV", "development"),
            database_url=os.getenv("UGAI_DATABASE_URL", "sqlite:///./ugai.db"),
            budget_default_usd=budget,
            max_context_tokens=int(os.getenv("UGAI_MAX_CONTEXT_TOKENS", "200000")),
            log_level=os.getenv("UGAI_LOG_LEVEL", "INFO"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL") or None,
            openai_model=os.getenv("OPENAI_MODEL") or None,
        )
