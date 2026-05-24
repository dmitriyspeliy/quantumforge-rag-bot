"""
Knowledge base document loader.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def extract_title(text: str, fallback: str) -> str:
    """
    Extract markdown title from document text.
    """

    for line in text.splitlines():
        normalized = line.strip()
        if normalized.startswith("# "):
            return normalized.removeprefix("# ").strip()

    return fallback


def load_knowledge_base(knowledge_base_dir: Path) -> list[Document]:
    """
    Load markdown/txt documents from local knowledge base.

    Metadata contains:
    - source: relative file path;
    - title: first markdown title or file stem;
    - file_name: original file name.
    """

    if not knowledge_base_dir.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {knowledge_base_dir}")

    documents: list[Document] = []

    for file_path in sorted(knowledge_base_dir.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        source = file_path.relative_to(knowledge_base_dir).as_posix()
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": source,
                    "title": extract_title(text, file_path.stem),
                    "file_name": file_path.name,
                },
            )
        )

    if not documents:
        raise ValueError(f"No knowledge base documents found in: {knowledge_base_dir}")

    return documents
