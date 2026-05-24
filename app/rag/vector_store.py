"""
FAISS vector store operations.
"""

from __future__ import annotations

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


def build_faiss_index(
    chunks: list[Document],
    embeddings: OpenAIEmbeddings,
    vectorstore_dir: Path,
) -> FAISS:
    """
    Build and persist FAISS index from document chunks.
    """

    if not chunks:
        raise ValueError("Cannot build FAISS index: chunks list is empty")

    vectorstore_dir.mkdir(parents=True, exist_ok=True)

    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(str(vectorstore_dir))

    return db


def load_faiss_index(
    embeddings: OpenAIEmbeddings,
    vectorstore_dir: Path,
) -> FAISS:
    """
    Load FAISS index from local directory.
    """

    if not vectorstore_dir.exists():
        raise FileNotFoundError(f"Vector store directory not found: {vectorstore_dir}")

    return FAISS.load_local(
        str(vectorstore_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )
