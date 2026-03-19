from __future__ import annotations

from pathlib import Path

from cos.core.models import Document


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".log", ".py", ".js", ".ts", ".json"}


def load_document_from_path(path: str) -> Document:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    ext = p.suffix.lower()
    if ext not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    content = p.read_text(encoding="utf-8")
    source_type = "code" if ext in {".py", ".js", ".ts"} else "text"
    return Document(source_type=source_type, source_uri=str(p.resolve()), content=content)
