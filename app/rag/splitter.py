"""
Document chunking utilities.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    documents: list[Document],
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
) -> list[Document]:
    """
    Split documents into chunks and enrich metadata with chunk ids.

    The selected size roughly corresponds to the assignment requirement:
    logical chunks around 100-300 words / 500-1000 tokens for small markdown docs.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_size"] = len(chunk.page_content)

    return chunks
