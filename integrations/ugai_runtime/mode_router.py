"""Deterministic mode routing based on task size and specialist needs."""
from __future__ import annotations
from enum import Enum

class Mode(str, Enum):
    FAST = "FAST"
    PLANNED = "PLANNED"
    ORCHESTRATED = "ORCHESTRATED"
    DYNAMIC = "DYNAMIC"

class ModeRouter:
    @staticmethod
    def select(files_affected: int, has_dependencies: bool = False,
               requires_specialists: bool = False,
               pattern_expressible_as_script: bool = False) -> Mode:
        if files_affected < 0:
            raise ValueError("files_affected must be non-negative")
        if files_affected > 10 and pattern_expressible_as_script:
            return Mode.DYNAMIC
        if files_affected > 10 or requires_specialists:
            return Mode.ORCHESTRATED
        if files_affected >= 2 or has_dependencies:
            return Mode.PLANNED
        return Mode.FAST
