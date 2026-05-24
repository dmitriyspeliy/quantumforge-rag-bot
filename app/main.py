"""
Console entrypoint for the RAG bot.
"""

from __future__ import annotations

from app.config import get_settings
from app.rag.chain import answer_question


def main() -> None:
    """
    Start simple REPL interface.
    """

    settings = get_settings()

    print("QuantumForge RAG Bot")
    print("Type your question. Type 'exit' to stop.")
    print("-" * 80)

    while True:
        question = input("Q: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("Bye.")
            break

        if not question:
            continue

        result = answer_question(question, settings)
        print("\nA:")
        print(result.answer)
        print("\nRetrieved chunks:")
        for source in result.sources:
            print(f"- {source.source}#{source.chunk_id}, score={source.score:.4f}, title={source.title}")
        print("-" * 80)


if __name__ == "__main__":
    main()
