"""Semantic retrieval over the institutional RAG index."""
from __future__ import annotations

import argparse
import json
import math
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

from integrations.rag.config import require_supabase_config

EXPECTED_EMBEDDING_DIMENSION = 384


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Natural-language search query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.top_k <= 50:
        raise SystemExit("--top-k must be between 1 and 50")
    query = args.query.strip()
    if not query:
        raise SystemExit("--query must contain non-whitespace text")

    url, key = require_supabase_config()
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
    if not model_name:
        raise SystemExit("EMBEDDING_MODEL cannot be empty")
    model = SentenceTransformer(model_name)
    model_dimension = model.get_sentence_embedding_dimension()
    if model_dimension != EXPECTED_EMBEDDING_DIMENSION:
        raise SystemExit(
            f"Embedding model dimension mismatch: database RPC expects {EXPECTED_EMBEDDING_DIMENSION}, "
            f"configured model reports {model_dimension}"
        )
    vector = model.encode(query, normalize_embeddings=True).tolist()
    if len(vector) != EXPECTED_EMBEDDING_DIMENSION or not all(math.isfinite(float(value)) for value in vector):
        raise SystemExit("Query embedding is invalid or has the wrong dimension")
    client = create_client(url, key)
    response = client.rpc("match_rag_chunks", {
        "query_embedding": vector,
        "match_count": args.top_k,
        "filter_metadata": {},
    }).execute()
    print(json.dumps(response.data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
