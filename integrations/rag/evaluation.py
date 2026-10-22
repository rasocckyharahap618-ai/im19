"""Offline retrieval evaluation metrics for Institutional RAG."""
from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

def reciprocal_rank(relevant_ranks: Sequence[int]) -> float:
    valid = [rank for rank in relevant_ranks if isinstance(rank, int) and rank > 0]
    return 1.0 / min(valid) if valid else 0.0

def precision_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    if k < 1:
        raise ValueError("k must be >= 1")
    top = list(retrieved[:k])
    return sum(item in relevant for item in top) / len(top) if top else 0.0

def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    if k < 1:
        raise ValueError("k must be >= 1")
    return len(set(retrieved[:k]) & relevant) / len(relevant) if relevant else 0.0

def evaluate_case(case: Mapping[str, Any], results: Sequence[Mapping[str, Any]], *, k: int = 5) -> dict[str, Any]:
    """Score retrieved chunks against expected source URIs and optional expected terms."""
    if k < 1:
        raise ValueError("k must be >= 1")
    expected_sources = set(case.get("relevant_source_uris") or [])
    expected_terms = [str(term).casefold() for term in (case.get("expected_terms") or [])]
    ranked_sources: list[str] = []
    term_hits: list[bool] = []
    for row in results[:k]:
        metadata = row.get("metadata") or {}
        source_uri = row.get("source_uri") or metadata.get("source_uri") or metadata.get("path") or ""
        ranked_sources.append(str(source_uri))
        content = str(row.get("content") or "").casefold()
        term_hits.append(all(term in content for term in expected_terms) if expected_terms else True)
    ranks = [i for i, uri in enumerate(ranked_sources, 1) if uri in expected_sources]
    return {
        "id": str(case.get("id", "")), "query": str(case.get("query", "")), "k": k,
        "retrieved_count": len(ranked_sources),
        "precision_at_k": precision_at_k(ranked_sources, expected_sources, k) if expected_sources else None,
        "recall_at_k": recall_at_k(ranked_sources, expected_sources, k) if expected_sources else None,
        "reciprocal_rank": reciprocal_rank(ranks), "relevant_source_found": bool(ranks),
        "expected_terms_coverage": sum(term_hits) / len(term_hits) if term_hits and expected_terms else None,
    }

def aggregate_metrics(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    if not materialized:
        return {"case_count": 0, "mrr": 0.0, "source_hit_rate": 0.0}
    return {
        "case_count": len(materialized),
        "mrr": sum(float(row.get("reciprocal_rank", 0.0)) for row in materialized) / len(materialized),
        "source_hit_rate": sum(bool(row.get("relevant_source_found")) for row in materialized) / len(materialized),
        "mean_precision_at_k": _mean_defined(materialized, "precision_at_k"),
        "mean_recall_at_k": _mean_defined(materialized, "recall_at_k"),
        "mean_expected_terms_coverage": _mean_defined(materialized, "expected_terms_coverage"),
    }

def _mean_defined(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None
