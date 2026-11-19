"""Evidence verification and conservative response gates."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class VerificationResult:
    verified: tuple[dict, ...]
    rejected: tuple[dict, ...]
    missing: tuple[str, ...]

class ClaimVerifier:
    @staticmethod
    def verify(claims: Iterable[dict], ledger: set[str]) -> VerificationResult:
        verified, rejected, missing = [], [], []
        for original in claims:
            claim = dict(original)
            evidence = str(claim.get("evidence", ""))
            if evidence == "[assume]":
                claim["status"] = "probable"
                verified.append(claim)
            elif evidence == "[unknown]":
                claim["status"] = "unknown"
                rejected.append(claim)
            elif evidence.startswith(("doc:", "cmd:")) and evidence not in ledger:
                missing.append(evidence)
                claim["status"] = "unverified"
                rejected.append(claim)
            elif claim.get("status") == "confirmed" and not evidence:
                claim["status"] = "unverified"
                rejected.append(claim)
            else:
                verified.append(claim)
        return VerificationResult(tuple(verified), tuple(rejected), tuple(dict.fromkeys(missing)))

@dataclass(frozen=True)
class GateResult:
    passed: bool
    violations: tuple[str, ...]

class GateChecker:
    NUMBER = re.compile(r"(?<![A-Za-z])\b\d+(?:\.\d+)?%?\b")
    ARTIFACT = re.compile(r"(?:[A-Za-z0-9_./-]+\.(?:py|js|ts|json|ya?ml|md)|/api/[A-Za-z0-9_./{}-]+)", re.I)
    HEDGE = re.compile(r"\b(mungkin|sepertinya|probably|perhaps|seems?)\b", re.I)
    RECOMMENDATION = re.compile(r"\b(recommend|recommended|should|sebaiknya|disarankan)\b", re.I)
    SCORE = re.compile(r"\b(?:score|skor|rating)\s*[:=]?\s*\d+(?:\.\d+)?", re.I)
    EXECUTION = re.compile(r"\b(test|tested|tests|lulus|passed|berhasil dijalankan)\b", re.I)

    @classmethod
    def check(cls, task_view: dict, ledger: set[str], response: dict) -> GateResult:
        violations = []
        answer = str(response.get("answer", ""))
        claims = response.get("claims", [])
        confirmed = [c for c in claims if c.get("status") == "confirmed"]
        if cls.NUMBER.search(answer):
            valid_meta = any(
                isinstance(c.get("number_meta"), dict)
                and all(c["number_meta"].get(k) for k in ("method", "source", "captured"))
                and c["number_meta"].get("n") is not None
                for c in claims
            )
            if not valid_meta:
                violations.append("G1: numeric statement lacks complete number_meta (method, n, source, captured)")
        if cls.ARTIFACT.search(answer):
            grounded = any(
                str(c.get("evidence", "")).startswith(("doc:", "cmd:", "api:"))
                and c.get("evidence") in ledger
                for c in claims
            )
            if not grounded:
                violations.append("G2: file/API reference lacks a ledger-backed evidence tag")
        if cls.EXECUTION.search(answer) and not any(c.get("execution_evidence") for c in claims):
            violations.append("G3: execution claim lacks execution_evidence")
        if confirmed and cls.HEDGE.search(answer):
            violations.append("G4: hedged language conflicts with confirmed claim status")
        if cls.RECOMMENDATION.search(answer) and not response.get("falsification_conditions"):
            violations.append("G5: recommendation lacks falsification condition")
        if cls.SCORE.search(answer) and not response.get("scoring_rubric"):
            violations.append("G6: score is presented without a scoring rubric")
        missing_sections = sorted(set(task_view.get("required_sections", [])) - set(response.get("covered_sections", [])))
        if missing_sections:
            violations.append("G7: required sections not covered: " + ", ".join(missing_sections))
        return GateResult(not violations, tuple(violations))
