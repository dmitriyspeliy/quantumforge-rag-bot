"""
Evaluate RAG bot quality using a golden question set.

The script:
1. Loads golden questions.
2. Runs each question through the RAG pipeline.
3. Applies artificial coverage gaps without deleting documents physically.
4. Writes JSONL logs for analysis.
5. Prints summary metrics.

Usage:
    python scripts/evaluate.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.chain import UNKNOWN_ANSWER, RagAnswer, answer_question
from app.rag.retriever import SearchResult


GOLDEN_QUESTIONS_PATH = PROJECT_ROOT / "data" / "evaluation" / "golden_questions.jsonl"
COVERAGE_GAPS_PATH = PROJECT_ROOT / "data" / "evaluation" / "coverage_gaps.json"
LOG_DIR = PROJECT_ROOT / "docs" / "task7_logs"
LOG_PATH = LOG_DIR / "rag_evaluation_logs.jsonl"
REPORT_PATH = LOG_DIR / "rag_evaluation_report.json"


@dataclass(frozen=True)
class GoldenQuestion:
    """
    One golden question test case.
    """

    id: str
    question: str
    expected_status: str
    expected_sources: list[str]
    expected_keywords: list[str]
    topic: str


@dataclass(frozen=True)
class EvaluationRecord:
    """
    One evaluation result record persisted to JSONL.
    """

    timestamp: str
    id: str
    question: str
    topic: str
    expected_status: str
    actual_status: str
    success: bool
    chunks_found: bool
    answer_length: int
    answer: str
    sources: list[str]
    blocked_sources: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    notes: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """
    Load JSONL file.
    """

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_golden_questions() -> list[GoldenQuestion]:
    """
    Load golden question set.
    """

    return [GoldenQuestion(**item) for item in load_jsonl(GOLDEN_QUESTIONS_PATH)]


def load_coverage_gaps() -> dict[str, Any]:
    """
    Load artificial coverage gaps config.
    """

    return json.loads(COVERAGE_GAPS_PATH.read_text(encoding="utf-8"))


def source_names(sources: list[SearchResult]) -> list[str]:
    """
    Return source file names from retrieved chunks.
    """

    return [item.source for item in sources]


def apply_artificial_gap(result: RagAnswer, excluded_sources: set[str], excluded_terms: list[str]) -> RagAnswer:
    """
    Simulate missing knowledge by excluding selected sources from evaluation context.

    This avoids physically deleting files from the knowledge base while still testing
    how the system behaves when key entities are absent.
    """

    question_lower = result.question.lower()

    has_excluded_term_in_question = any(term.lower() in question_lower for term in excluded_terms)
    safe_sources = [item for item in result.sources if item.source not in excluded_sources]

    if has_excluded_term_in_question:
        return RagAnswer(
            question=result.question,
            answer=UNKNOWN_ANSWER,
            sources=safe_sources,
            blocked_sources=result.blocked_sources,
        )

    return RagAnswer(
        question=result.question,
        answer=result.answer,
        sources=safe_sources,
        blocked_sources=result.blocked_sources,
    )


def classify_answer(answer: str) -> str:
    """
    Classify answer as answer/unknown.
    """

    if answer.strip() == UNKNOWN_ANSWER:
        return "unknown"

    return "answer"


def evaluate_keywords(answer: str, expected_keywords: list[str]) -> tuple[list[str], list[str]]:
    """
    Check keyword coverage in answer.
    """

    answer_lower = answer.lower()
    matched: list[str] = []
    missing: list[str] = []

    for keyword in expected_keywords:
        if keyword.lower() in answer_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)

    return matched, missing


def evaluate_sources(actual_sources: list[str], expected_sources: list[str]) -> bool:
    """
    Check that at least one expected source was retrieved.
    """

    if not expected_sources:
        return True

    return any(source in actual_sources for source in expected_sources)


def evaluate_case(case: GoldenQuestion, excluded_sources: set[str], excluded_terms: list[str]) -> EvaluationRecord:
    """
    Run one golden question through the bot and evaluate result.
    """

    settings = get_settings()
    raw_result = answer_question(case.question, settings)
    result = apply_artificial_gap(raw_result, excluded_sources, excluded_terms)

    actual_status = classify_answer(result.answer)
    sources = source_names(result.sources)
    blocked_sources = source_names(result.blocked_sources)

    matched_keywords, missing_keywords = evaluate_keywords(result.answer, case.expected_keywords)

    status_ok = actual_status == case.expected_status
    source_ok = evaluate_sources(sources, case.expected_sources)

    if case.expected_status == "answer":
        keywords_ok = len(missing_keywords) == 0
    else:
        keywords_ok = True

    success = status_ok and source_ok and keywords_ok

    notes: list[str] = []
    if not status_ok:
        notes.append(f"Expected status {case.expected_status}, got {actual_status}")
    if not source_ok:
        notes.append(f"Expected one of sources {case.expected_sources}, got {sources}")
    if missing_keywords:
        notes.append(f"Missing keywords: {missing_keywords}")

    return EvaluationRecord(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        id=case.id,
        question=case.question,
        topic=case.topic,
        expected_status=case.expected_status,
        actual_status=actual_status,
        success=success,
        chunks_found=len(sources) > 0,
        answer_length=len(result.answer),
        answer=result.answer,
        sources=sources,
        blocked_sources=blocked_sources,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        notes="; ".join(notes),
    )


def build_report(records: list[EvaluationRecord]) -> dict[str, Any]:
    """
    Build aggregate evaluation report.
    """

    total = len(records)
    passed = sum(1 for item in records if item.success)
    failed = total - passed

    by_topic: dict[str, dict[str, int]] = {}
    for item in records:
        bucket = by_topic.setdefault(item.topic, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        if item.success:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1

    unanswered = [
        {
            "id": item.id,
            "question": item.question,
            "topic": item.topic,
            "sources": item.sources,
            "notes": item.notes,
        }
        for item in records
        if item.actual_status == "unknown"
    ]

    failed_cases = [
        {
            "id": item.id,
            "question": item.question,
            "topic": item.topic,
            "expected_status": item.expected_status,
            "actual_status": item.actual_status,
            "sources": item.sources,
            "notes": item.notes,
        }
        for item in records
        if not item.success
    ]

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "by_topic": by_topic,
        "unanswered_count": len(unanswered),
        "unanswered": unanswered,
        "failed_cases": failed_cases,
        "recommendations": [
            "Restore or improve documents for artificial gaps: Xarn Velgor, Void Core, Synth Flux.",
            "Add more documents for external corporate integrations if QuantumForge/Snowflake questions are expected.",
            "Review cases where retrieved sources are semantically close but do not contain the exact expected answer.",
            "Keep golden_questions.jsonl under version control and run evaluation after every index update."
        ],
    }


def main() -> None:
    """
    Run evaluation and persist logs.
    """

    gaps = load_coverage_gaps()
    excluded_sources = set(gaps["excluded_sources"])
    excluded_terms = gaps["excluded_terms"]

    questions = load_golden_questions()
    records = [
        evaluate_case(case, excluded_sources=excluded_sources, excluded_terms=excluded_terms)
        for case in questions
    ]

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    LOG_PATH.write_text(
        "\n".join(json.dumps(asdict(item), ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )

    report = build_report(records)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"JSONL log saved to: {LOG_PATH}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
