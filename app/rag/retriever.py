"""
Search helpers for FAISS index.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_community.vectorstores import FAISS


@dataclass(frozen=True)
class SearchResult:
    """
    User-friendly search result DTO.
    """

    source: str
    title: str
    chunk_id: int
    score: float
    content: str


def search_index(db: FAISS, query: str, top_k: int = 4) -> list[SearchResult]:
    """
    Search relevant chunks in FAISS index.

    Lower score means closer vector distance for this FAISS setup.
    """

    raw_results = db.similarity_search_with_score(query, k=top_k)

    results: list[SearchResult] = []
    for document, score in raw_results:
        metadata = document.metadata
        results.append(
            SearchResult(
                source=str(metadata.get("source", "unknown")),
                title=str(metadata.get("title", "unknown")),
                chunk_id=int(metadata.get("chunk_id", -1)),
                score=float(score),
                content=document.page_content,
            )
        )

    return results
