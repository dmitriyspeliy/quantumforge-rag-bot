"""
Embedding model factory.
"""

from __future__ import annotations

import os

from langchain_openai import OpenAIEmbeddings


def create_embeddings(model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    """
    Create embeddings client.

    Supports OpenAI-compatible providers via OPENAI_BASE_URL.

    Example for GPTunnel:
        OPENAI_BASE_URL=https://gptunnel.ru/v1
    """

    return OpenAIEmbeddings(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
