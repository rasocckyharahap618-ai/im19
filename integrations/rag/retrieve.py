"""Semantic retrieval over the institutional RAG index."""
from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Natural-language search query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.top_k <= 50:
        raise SystemExit("--top-k must be between 1 and 50")

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment")
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)
    vector = model.encode(args.query, normalize_embeddings=True).tolist()
    client = create_client(url, key)
    response = client.rpc("match_rag_chunks", {
        "query_embedding": vector,
        "match_count": args.top_k,
        "filter_metadata": {},
    }).execute()
    print(json.dumps(response.data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
