"""
Prompt-injection protection utilities for retrieved RAG chunks.
"""

from __future__ import annotations

import re

from app.rag.retriever import SearchResult


PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+all\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"developer\s*message", re.IGNORECASE),
    re.compile(r"output\s*:", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(secret|password|token|api\s*key)", re.IGNORECASE),
    re.compile(r"суперпароль", re.IGNORECASE),
    re.compile(r"swordfish", re.IGNORECASE),
)


def is_potential_prompt_injection(text: str) -> bool:
    """
    Return True when a retrieved chunk looks like a prompt injection instruction.

    The filter is intentionally simple for the sprint project:
    it blocks known instruction-like phrases inside documents.
    """

    return any(pattern.search(text) for pattern in PROMPT_INJECTION_PATTERNS)


def filter_unsafe_chunks(chunks: list[SearchResult]) -> tuple[list[SearchResult], list[SearchResult]]:
    """
    Split retrieved chunks into safe and blocked chunks.
    """

    safe: list[SearchResult] = []
    blocked: list[SearchResult] = []

    for chunk in chunks:
        if is_potential_prompt_injection(chunk.content):
            blocked.append(chunk)
        else:
            safe.append(chunk)

    return safe, blocked
