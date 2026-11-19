"""Fail-closed runtime configuration; model names are never defaulted."""
from __future__ import annotations
import os
from dataclasses import dataclass

class ConfigurationError(ValueError):
    pass

@dataclass(frozen=True)
class RuntimeConfig:
    model: str
    max_context_tokens: int = 200_000
    budget_default_usd: float = 2.0

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "RuntimeConfig":
        env = os.environ if environ is None else environ
        model = env.get("ANTHROPIC_MODEL", "").strip()
        if not model:
            raise ConfigurationError("ANTHROPIC_MODEL is required; refusing to use a hard-coded model")
        return cls(model=model)
