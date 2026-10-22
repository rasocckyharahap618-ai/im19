"""Deterministic document-quality and chunking primitives for Institutional RAG."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class QualityReport:
    accepted: bool
    reasons: tuple[str, ...]
    character_count: int
    word_count: int
    content_hash: str

def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without rewriting meaning."""
    if not isinstance(text, str):
        raise TypeError("Document text must be a string.")
    text = unicodedata.normalize("NFKC", text).replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def sha256_text(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def assess_document(text: str, *, min_characters: int = 80, max_characters: int = 5_000_000) -> QualityReport:
    """Reject empty, too-short, oversized, and likely corrupted extraction output."""
    if min_characters < 0 or max_characters < 1 or min_characters > max_characters:
        raise ValueError("Invalid document quality limits.")
    normalized = normalize_text(text)
    reasons: list[str] = []
    if not normalized:
        reasons.append("empty_after_normalization")
    if len(normalized) < min_characters:
        reasons.append("below_minimum_character_count")
    if len(normalized) > max_characters:
        reasons.append("above_maximum_character_count")
    if normalized:
        printable_ratio = sum(ch.isprintable() or ch in "\n\t" for ch in normalized) / len(normalized)
        if printable_ratio < 0.98:
            reasons.append("low_printable_character_ratio")
        words = re.findall(r"\b[\w'-]+\b", normalized, flags=re.UNICODE)
        if len(words) >= 30:
            non_space = sum(not ch.isspace() for ch in normalized)
            alpha_ratio = sum(ch.isalpha() for ch in normalized) / max(1, non_space)
            if alpha_ratio < 0.15:
                reasons.append("low_alphabetic_character_ratio")
    else:
        words = []
    return QualityReport(not reasons, tuple(reasons), len(normalized), len(words), sha256_text(normalized))

def chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 120) -> list[dict[str, Any]]:
    """Create deterministic overlapping character chunks with stable local IDs."""
    normalized = normalize_text(text)
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size.")
    if not normalized:
        return []
    chunks: list[dict[str, Any]] = []
    start, index, length = 0, 0, len(normalized)
    while start < length:
        hard_end = min(start + chunk_size, length)
        end = hard_end
        if hard_end < length:
            floor = start + max(1, int(chunk_size * 0.65))
            candidates = [
                normalized.rfind("\n\n", floor, hard_end),
                normalized.rfind(". ", floor, hard_end),
                normalized.rfind("? ", floor, hard_end),
                normalized.rfind("! ", floor, hard_end),
                normalized.rfind(" ", floor, hard_end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (2 if normalized[boundary:boundary + 2] == "\n\n" else 1)
        content = normalized[start:end].strip()
        if content:
            chunks.append({
                "chunk_index": index, "content": content,
                "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "character_start": start, "character_end": end,
                "character_count": len(content),
            })
            index += 1
        if end >= length:
            break
        next_start = max(start + 1, end - overlap)
        whitespace = normalized.find(" ", next_start, min(next_start + 80, length))
        start = whitespace + 1 if whitespace >= 0 else next_start
    return chunks

def build_provenance(*, source_uri: str, source_version: str | None, title: str,
                     text: str, source_modified_at: str | None = None) -> dict[str, Any]:
    """Build reproducible provenance metadata; never stores source bytes."""
    if not source_uri or not source_uri.strip():
        raise ValueError("source_uri is required.")
    normalized = normalize_text(text)
    report = assess_document(normalized)
    return {
        "source_uri": source_uri.strip(), "source_version": (source_version or "unknown").strip(),
        "title": title.strip() or "Untitled document", "content_hash": report.content_hash,
        "character_count": report.character_count, "word_count": report.word_count,
        "quality_accepted": report.accepted, "quality_reasons": list(report.reasons),
        "source_modified_at": source_modified_at,
        "mined_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "im19-institutional-rag-mining-v1",
    }

def quality_report_dict(report: QualityReport) -> dict[str, Any]:
    result = asdict(report)
    result["reasons"] = list(report.reasons)
    return result
