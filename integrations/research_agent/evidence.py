"""In-memory evidence ledger with stable IDs and provenance metadata."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable
from uuid import uuid4

@dataclass(frozen=True)
class EvidenceRecord:
    source: str
    title: str
    locator: str
    excerpt: str = ""
    doi: str | None = None
    published_at: str | None = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    content_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.title.strip() or not self.locator.strip():
            raise ValueError("source, title, and locator are required")
        if self.excerpt and not self.content_sha256:
            object.__setattr__(self, "content_sha256", sha256(self.excerpt.encode("utf-8")).hexdigest())

class EvidenceLedger:
    """Append-only in-memory evidence collection; persistence is deferred."""
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def add(self, record: EvidenceRecord) -> EvidenceRecord:
        existing = self._records.get(record.evidence_id)
        if existing is not None and existing != record:
            raise ValueError("evidence_id collision with different content")
        self._records[record.evidence_id] = record
        return record

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        return self._records.get(evidence_id)

    def require(self, evidence_ids: Iterable[str]) -> list[EvidenceRecord]:
        records, missing = [], []
        for evidence_id in evidence_ids:
            record = self.get(evidence_id)
            if record is None:
                missing.append(evidence_id)
            else:
                records.append(record)
        if missing:
            raise KeyError(f"unknown evidence IDs: {', '.join(missing)}")
        return records

    def list(self) -> list[EvidenceRecord]:
        return list(self._records.values())

    def export(self) -> list[dict]:
        return [asdict(record) for record in self._records.values()]
