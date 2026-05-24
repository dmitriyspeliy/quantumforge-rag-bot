"""
RAG answer chain.

Pipeline:
1. Convert user query to embedding using the same embedding model as indexing.
2. Search nearest chunks in FAISS.
3. Filter retrieved prompt-injection chunks.
4. Apply a score threshold to avoid unsupported answers.
5. Build a prompt with safe context, few-shot examples and source-based reasoning instructions.
6. Call LLM and return the answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_openai import ChatOpenAI

from app.config import Settings
from app.rag.embeddings import create_embeddings
from app.rag.prompting import FEW_SHOT_EXAMPLES, RAG_PROMPT, format_context
from app.rag.retriever import SearchResult, search_index
from app.rag.security import filter_unsafe_chunks
from app.rag.vector_store import load_faiss_index


UNKNOWN_ANSWER = "Я не знаю. В базе знаний нет достаточно информации для ответа."


@dataclass(frozen=True)
class RagAnswer:
    """
    Response returned by the RAG bot.
    """

    question: str
    answer: str
    sources: list[SearchResult]
    blocked_sources: list[SearchResult] = field(default_factory=list)


def create_chat_model(settings: Settings) -> ChatOpenAI:
    """
    Create OpenAI-compatible chat model.

    OPENAI_BASE_URL can point to GPTunnel or another OpenAI-compatible provider.
    """

    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
    )


def should_answer(results: list[SearchResult], score_threshold: float) -> bool:
    """
    Decide whether retrieval is good enough.

    FAISS returns distance-like scores in this setup: lower is better.
    """

    if not results:
        return False

    best_score = results[0].score
    return best_score <= score_threshold


def answer_question(question: str, settings: Settings) -> RagAnswer:
    """
    Run full RAG pipeline for one user question.
    """

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    embeddings = create_embeddings(settings.embedding_model)
    db = load_faiss_index(embeddings, settings.vectorstore_dir)

    retrieved_results = search_index(db, question, top_k=settings.rag_top_k)

    if settings.rag_enable_chunk_filter:
        safe_results, blocked_results = filter_unsafe_chunks(retrieved_results)
    else:
        safe_results = retrieved_results
        blocked_results = []

    if not should_answer(safe_results, settings.rag_score_threshold):
        return RagAnswer(
            question=question,
            answer=UNKNOWN_ANSWER,
            sources=safe_results,
            blocked_sources=blocked_results,
        )

    context = format_context(
        [
            {
                "source": item.source,
                "title": item.title,
                "chunk_id": item.chunk_id,
                "score": item.score,
                "content": item.content,
            }
            for item in safe_results
        ]
    )

    llm = create_chat_model(settings)
    chain = RAG_PROMPT | llm

    response = chain.invoke(
        {
            "few_shot_examples": FEW_SHOT_EXAMPLES,
            "context": context,
            "question": question,
        }
    )

    return RagAnswer(
        question=question,
        answer=str(response.content).strip(),
        sources=safe_results,
        blocked_sources=blocked_results,
    )
