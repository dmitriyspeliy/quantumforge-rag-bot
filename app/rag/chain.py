"""
RAG answer chain.

Pipeline:
1. Convert user query to embedding using the same embedding model as indexing.
2. Search nearest chunks in FAISS.
3. Apply a score threshold to avoid unsupported answers.
4. Build a prompt with context, few-shot examples and concise source-based reasoning instructions.
5. Call LLM and return the answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from app.config import Settings
from app.rag.embeddings import create_embeddings
from app.rag.prompting import FEW_SHOT_EXAMPLES, RAG_PROMPT, format_context
from app.rag.retriever import SearchResult, search_index
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

    results = search_index(db, question, top_k=settings.rag_top_k)

    if not should_answer(results, settings.rag_score_threshold):
        return RagAnswer(
            question=question,
            answer=UNKNOWN_ANSWER,
            sources=results,
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
            for item in results
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
        sources=results,
    )
