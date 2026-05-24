"""
Generate transformed knowledge base for the QuantumForge RAG bot.

The script applies terms_map.json replacements to source markdown documents.
Usage:
    python scripts/replace_terms.py --source raw_knowledge_base --target data/knowledge_base --map data/knowledge_base/terms_map.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def replace_terms(text: str, terms_map: dict[str, str]) -> str:
    """
    Replace source-world terms with fictional terms.

    Longer terms are replaced first to avoid partial replacements.
    For example, "Emperor Palpatine" should be replaced before "Palpatine".
    """
    for source_term in sorted(terms_map.keys(), key=len, reverse=True):
        target_term = terms_map[source_term]
        text = re.sub(rf"\b{re.escape(source_term)}\b", target_term, text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Directory with raw .md/.txt source documents")
    parser.add_argument("--target", required=True, help="Directory for transformed documents")
    parser.add_argument("--map", required=True, help="Path to terms_map.json")
    args = parser.parse_args()

    source_dir = Path(args.source)
    target_dir = Path(args.target)
    map_path = Path(args.map)

    target_dir.mkdir(parents=True, exist_ok=True)

    terms_map = json.loads(map_path.read_text(encoding="utf-8"))

    for source_file in sorted(source_dir.glob("*")):
        if source_file.suffix.lower() not in {".md", ".txt"}:
            continue

        original_text = source_file.read_text(encoding="utf-8")
        transformed_text = replace_terms(original_text, terms_map)

        target_file = target_dir / source_file.name
        target_file.write_text(transformed_text, encoding="utf-8")

    print(f"Knowledge base generated in: {target_dir}")


if __name__ == "__main__":
    main()
