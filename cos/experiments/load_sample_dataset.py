from __future__ import annotations

import argparse
import json
from pathlib import Path

from cos.configs.settings import get_settings
from cos.core.models import IngestionRequest
from cos.runtime import COSRuntime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load sample dataset into C-OS runtime.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("datasets/sample_memory_notes.jsonl"),
        help="Path to JSONL dataset file.",
    )
    return parser.parse_args()


def load_dataset(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def run(dataset_path: Path) -> None:
    runtime = COSRuntime(get_settings())
    rows = load_dataset(dataset_path)
    statements = 0
    contradictions = 0

    for row in rows:
        request = IngestionRequest(**row)
        result = runtime.ingest_text(request)
        statements += result.statement_count
        contradictions += result.contradictions

    print(f"Loaded notes: {len(rows)}")
    print(f"Statements created: {statements}")
    print(f"Contradictions tracked: {contradictions}")


if __name__ == "__main__":
    args = parse_args()
    run(args.dataset)
