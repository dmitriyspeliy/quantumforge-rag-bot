"""
Daily knowledge base update script.

The script simulates production-like update flow:
1. Scan source directory with incoming documents.
2. Detect new or changed files using SHA-256 manifest.
3. Copy new/changed files into data/knowledge_base.
4. Rebuild FAISS index using the same chunking and embedding model.
5. Save JSON log with update result.

Usage:
    python scripts/update_index.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.rag.embeddings import create_embeddings
from app.rag.loader import load_knowledge_base
from app.rag.splitter import split_documents
from app.rag.vector_store import build_faiss_index


SUPPORTED_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class FileChange:
    """
    Description of a detected source file change.
    """

    path: str
    sha256: str
    status: str


@dataclass(frozen=True)
class UpdateLog:
    """
    JSON-serializable index update log.
    """

    started_at: str
    finished_at: str
    duration_sec: float
    source_dir: str
    knowledge_base_dir: str
    vectorstore_dir: str
    embedding_model: str
    files_scanned: int
    files_added_or_changed: int
    documents_loaded: int
    chunks_indexed: int
    index_files: list[str]
    errors: list[str]
    changed_files: list[dict[str, Any]]


def sha256_file(path: Path) -> str:
    """
    Calculate SHA-256 hash for a file.
    """

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, str]:
    """
    Load update manifest from JSON file.
    """

    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict[str, str]) -> None:
    """
    Save update manifest to JSON file.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def scan_source(source_dir: Path, previous_manifest: dict[str, str]) -> tuple[list[Path], list[FileChange], int]:
    """
    Scan source directory and return new/changed files.
    """

    changed_paths: list[Path] = []
    changes: list[FileChange] = []
    files_scanned = 0

    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(source_dir.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        files_scanned += 1
        relative_path = file_path.relative_to(source_dir).as_posix()
        current_hash = sha256_file(file_path)
        previous_hash = previous_manifest.get(relative_path)

        if previous_hash != current_hash:
            status = "added" if previous_hash is None else "changed"
            changed_paths.append(file_path)
            changes.append(FileChange(path=relative_path, sha256=current_hash, status=status))

    return changed_paths, changes, files_scanned


def copy_changed_files(changed_paths: list[Path], source_dir: Path, target_dir: Path) -> None:
    """
    Copy changed source files to the knowledge base directory.
    """

    target_dir.mkdir(parents=True, exist_ok=True)

    for source_file in changed_paths:
        relative_path = source_file.relative_to(source_dir)
        target_file = target_dir / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)


def rebuild_index() -> tuple[int, int, list[str]]:
    """
    Rebuild FAISS index from the current knowledge base.
    """

    settings = get_settings()

    documents = load_knowledge_base(settings.knowledge_base_dir)
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    embeddings = create_embeddings(settings.embedding_model)
    build_faiss_index(chunks, embeddings, settings.vectorstore_dir)

    index_files = [
        item.name
        for item in sorted(settings.vectorstore_dir.glob("*"))
        if item.is_file()
    ]

    return len(documents), len(chunks), index_files


def main() -> None:
    """
    Run daily index update.
    """

    settings = get_settings()

    source_dir = PROJECT_ROOT / "data" / "incoming_docs"
    log_dir = PROJECT_ROOT / "docs" / "task6_logs"
    manifest_path = log_dir / "index_manifest.json"
    log_path = log_dir / "update_index.log.json"

    errors: list[str] = []
    started = time.perf_counter()
    started_at = datetime.now().isoformat(timespec="seconds")

    files_scanned = 0
    changed_files: list[FileChange] = []
    documents_loaded = 0
    chunks_indexed = 0
    index_files: list[str] = []

    try:
        previous_manifest = load_manifest(manifest_path)
        changed_paths, changed_files, files_scanned = scan_source(source_dir, previous_manifest)

        copy_changed_files(changed_paths, source_dir, settings.knowledge_base_dir)

        documents_loaded, chunks_indexed, index_files = rebuild_index()

        next_manifest = dict(previous_manifest)
        for changed_file in changed_files:
            next_manifest[changed_file.path] = changed_file.sha256

        save_manifest(manifest_path, next_manifest)

    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    finished_at = datetime.now().isoformat(timespec="seconds")
    duration = time.perf_counter() - started

    update_log = UpdateLog(
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round(duration, 2),
        source_dir=str(source_dir.relative_to(PROJECT_ROOT)),
        knowledge_base_dir=str(settings.knowledge_base_dir),
        vectorstore_dir=str(settings.vectorstore_dir),
        embedding_model=settings.embedding_model,
        files_scanned=files_scanned,
        files_added_or_changed=len(changed_files),
        documents_loaded=documents_loaded,
        chunks_indexed=chunks_indexed,
        index_files=index_files,
        errors=errors,
        changed_files=[asdict(item) for item in changed_files],
    )

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(asdict(update_log), ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(asdict(update_log), ensure_ascii=False, indent=2))

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
