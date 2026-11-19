"""Output validation gates for research answers."""
from __future__ import annotations
import re
from dataclasses import dataclass
from .evidence import EvidenceLedger

class GuardViolation(ValueError):
    """Raised when an answer fails a research integrity check."""

_CITATION_PATTERN = re.compile(r"\[(EV-[A-Za-z0-9_-]+)\]")

@dataclass(frozen=True)
class GuardReport:
    valid: bool
    referenced_evidence_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()

class EvidenceGuard:
    """Resolve citation markers; this does not prove claim-level support."""
    def __init__(self, ledger: EvidenceLedger) -> None:
        self.ledger = ledger

    def validate(self, answer: str, required: bool = True) -> GuardReport:
        ids = tuple(dict.fromkeys(_CITATION_PATTERN.findall(answer)))
        if required and not ids:
            raise GuardViolation("answer requires at least one evidence citation")
        try:
            self.ledger.require(ids)
        except KeyError as exc:
            raise GuardViolation(str(exc)) from exc
        return GuardReport(valid=True, referenced_evidence_ids=ids)

    @staticmethod
    def require_human_review(action: str) -> None:
        gated = {"submit_manuscript", "send_to_journal", "publish", "delete_source"}
        if action in gated:
            raise GuardViolation(f"human approval required for action: {action}")
