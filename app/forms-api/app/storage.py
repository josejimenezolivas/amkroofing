"""Document store.

Locally, one JSON file per document under `forms-api/data/documents`.
On Vercel the container disk does not survive scale-to-zero, so when
`BLOB_READ_WRITE_TOKEN` is set each document is a private blob instead.
"""

import json
import uuid
from datetime import datetime, timezone

from . import blobstore
from .config import DOCUMENTS_DIR
from .models import Document, DocumentData, DocumentSummary


def _path(document_id: str):
    return DOCUMENTS_DIR / f"{document_id}.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load(raw: str) -> Document | None:
    try:
        return Document.model_validate_json(raw)
    except ValueError:
        return None


def list_documents() -> list[DocumentSummary]:
    docs: list[Document] = []
    if blobstore.enabled():
        for raw in blobstore.read_all():
            doc = _load(raw)
            if doc is not None:
                docs.append(doc)
    else:
        for path in DOCUMENTS_DIR.glob("*.json"):
            try:
                doc = _load(path.read_text())
            except OSError:
                continue
            if doc is not None:
                docs.append(doc)
    docs.sort(key=lambda d: d.updated_at, reverse=True)
    return [DocumentSummary(**d.model_dump()) for d in docs]


def get_document(document_id: str) -> Document | None:
    if blobstore.enabled():
        raw = blobstore.read_text(document_id)
        return _load(raw) if raw is not None else None
    path = _path(document_id)
    if not path.exists():
        return None
    return _load(path.read_text())


def create_document(template: str, style: str, title: str, data: DocumentData) -> Document:
    now = _now()
    doc = Document(
        id=uuid.uuid4().hex[:12],
        template=template,  # type: ignore[arg-type]
        style=style,  # type: ignore[arg-type]
        title=title,
        created_at=now,
        updated_at=now,
        data=data,
    )
    _write(doc)
    return doc


def save_document(
    doc: Document, data: DocumentData, title: str | None, style: str | None = None
) -> Document:
    doc.data = data
    if title is not None:
        doc.title = title
    if style is not None:
        doc.style = style  # type: ignore[assignment]
    doc.updated_at = _now()
    _write(doc)
    return doc


def seed_reference_documents() -> None:
    """Put the transcribed reference documents in the list if they are missing.

    Called on startup. Each has a fixed id, so edits to them survive a restart
    and only a deleted one comes back.
    """
    from .reference import REFERENCE_DOCUMENTS

    now = _now()
    for spec in REFERENCE_DOCUMENTS:
        if get_document(spec["id"]) is not None:
            continue
        _write(
            Document(
                id=spec["id"],
                template=spec["template"],
                style="classic",
                title=spec["title"],
                created_at=now,
                updated_at=now,
                data=spec["data"],
            )
        )


def delete_document(document_id: str) -> bool:
    if blobstore.enabled():
        return blobstore.delete_pathname(document_id)
    path = _path(document_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def _write(doc: Document) -> None:
    payload = json.loads(doc.model_dump_json())
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if blobstore.enabled():
        blobstore.put_text(doc.id, text)
        return
    _path(doc.id).write_text(text)
