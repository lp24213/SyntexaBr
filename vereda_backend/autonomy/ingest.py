from dataclasses import dataclass


@dataclass
class IngestResult:
    source_id: str
    chunks: int
    ok: bool


def ingest_document(source_id: str, raw_text: str) -> IngestResult:
    """
    Pipeline mínimo para tokenização/chunking futuro.
    """
    chunks = max(1, len((raw_text or "").split()) // 180)
    return IngestResult(source_id=source_id, chunks=chunks, ok=True)
