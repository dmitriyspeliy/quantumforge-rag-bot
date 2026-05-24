"""
Ask the RAG bot one question from CLI.

Usage:
    python scripts/ask_bot.py "Who was Xarn Velgor?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.chain import answer_question


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="User question")
    args = parser.parse_args()

    settings = get_settings()
    result = answer_question(args.question, settings)

    print("Question:")
    print(result.question)
    print()
    print("Answer:")
    print(result.answer)
    print()

    if result.blocked_sources:
        print("Blocked chunks:")
        for source in result.blocked_sources:
            print(f"- {source.source}#{source.chunk_id}, score={source.score:.4f}, title={source.title}")
        print()

    print("Retrieved safe chunks:")
    for source in result.sources:
        print(f"- {source.source}#{source.chunk_id}, score={source.score:.4f}, title={source.title}")


if __name__ == "__main__":
    main()
