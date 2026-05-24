from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.embeddings import create_embeddings
from app.rag.loader import load_knowledge_base
from app.rag.splitter import split_documents
from app.rag.vector_store import build_faiss_index


def main() -> None:
    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Create .env from .env.example and fill the key.")

    started_at = time.perf_counter()

    documents = load_knowledge_base(settings.knowledge_base_dir)
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    embeddings = create_embeddings(settings.embedding_model)
    build_faiss_index(chunks, embeddings, settings.vectorstore_dir)

    elapsed = time.perf_counter() - started_at

    print("FAISS index created successfully")
    print(f"Knowledge base directory: {settings.knowledge_base_dir}")
    print(f"Vector store directory: {settings.vectorstore_dir}")
    print(f"Embedding model: {settings.embedding_model}")
    print("Embedding dimensions: 1536")
    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks indexed: {len(chunks)}")
    print(f"Generation time: {elapsed:.2f} sec")


if __name__ == "__main__":
    main()
