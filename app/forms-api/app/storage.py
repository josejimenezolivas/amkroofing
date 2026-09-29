"""Document store: the `forms.documents` table."""

import uuid

from psycopg.types.json import Jsonb

from . import db
from .models import Document, DocumentData, DocumentSummary


def _data(data: DocumentData) -> Jsonb:
    return Jsonb(data.model_dump(mode="json"))


def list_documents() -> list[DocumentSummary]:
    found = db.rows(
        "select id, template, style, title, created_at, updated_at"
        " from forms.documents order by updated_at desc"
    )
    return [DocumentSummary.model_validate(r) for r in found]


def get_document(document_id: str) -> Document | None:
    found = db.row("select * from forms.documents where id = %s", (document_id,))
    return Document.model_validate(found) if found else None


def create_document(template: str, style: str, title: str, data: DocumentData) -> Document:
    created = db.row(
        "insert into forms.documents (id, template, style, title, data)"
        " values (%s, %s, %s, %s, %s) returning *",
        (uuid.uuid4().hex[:12], template, style, title, _data(data)),
    )
    return Document.model_validate(created)


def save_document(
    doc: Document, data: DocumentData, title: str | None, style: str | None = None
) -> Document:
    saved = db.row(
        "update forms.documents"
        " set data = %s, title = coalesce(%s, title), style = coalesce(%s, style), updated_at = now()"
        " where id = %s returning *",
        (_data(data), title, style, doc.id),
    )
    return Document.model_validate(saved) if saved else doc


def seed_reference_documents() -> None:
    """Put the transcribed reference documents in the list if they are missing.

    Called on startup. Each has a fixed id, so edits to them survive a restart
    and only a deleted one comes back.
    """
    from .reference import REFERENCE_DOCUMENTS

    for spec in REFERENCE_DOCUMENTS:
        db.execute(
            "insert into forms.documents (id, template, style, title, data)"
            " values (%s, %s, 'classic', %s, %s) on conflict (id) do nothing",
            (spec["id"], spec["template"], spec["title"], _data(DocumentData.model_validate(spec["data"]))),
        )


def delete_document(document_id: str) -> bool:
    return db.execute("delete from forms.documents where id = %s", (document_id,)) > 0
