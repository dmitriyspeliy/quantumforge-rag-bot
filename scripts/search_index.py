from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.embeddings import create_embeddings
from app.rag.retriever import search_index
from app.rag.vector_store import load_faiss_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=None, help="Number of chunks to return")
    args = parser.parse_args()

    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Create .env from .env.example and fill the key.")

    embeddings = create_embeddings(settings.embedding_model)
    db = load_faiss_index(embeddings, settings.vectorstore_dir)

    results = search_index(db, args.query, top_k=args.top_k or settings.rag_top_k)

    print(f"Query: {args.query}")
    print(f"Results: {len(results)}")
    print("-" * 80)

    for result in results:
        preview = result.content.replace("\n", " ")[:500]
        print(f"source={result.source}")
        print(f"title={result.title}")
        print(f"chunk_id={result.chunk_id}")
        print(f"score={result.score:.4f}")
        print(f"text={preview}")
        print("-" * 80)


if __name__ == "__main__":
    main()
