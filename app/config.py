"""
Application configuration for the QuantumForge RAG bot.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)


@dataclass(frozen=True)
class Settings:
    """
    Runtime settings loaded from environment variables.
    """

    openai_api_key: str
    openai_base_url: str | None
    knowledge_base_dir: Path
    vectorstore_dir: Path
    embedding_model: str
    chat_model: str
    chunk_size: int
    chunk_overlap: int
    rag_top_k: int
    rag_score_threshold: float
    rag_enable_chunk_filter: bool


def _as_bool(value: str | None, default: bool = True) -> bool:
    """
    Convert environment string to boolean.
    """

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    """
    Build immutable application settings from environment variables.
    """

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=(os.getenv("OPENAI_BASE_URL") or "").strip() or None,
        knowledge_base_dir=Path(os.getenv("KNOWLEDGE_BASE_DIR", "data/knowledge_base")),
        vectorstore_dir=Path(os.getenv("VECTORSTORE_DIR", "vectorstore")),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip(),
        chat_model=os.getenv("CHAT_MODEL", "gpt-4.1-mini").strip(),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
        rag_top_k=int(os.getenv("RAG_TOP_K", "4")),
        rag_score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.85")),
        rag_enable_chunk_filter=_as_bool(os.getenv("RAG_ENABLE_CHUNK_FILTER"), default=True),
    )
