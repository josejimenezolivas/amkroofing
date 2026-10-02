from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import Document, DocumentCreate, DocumentSummary, DocumentUpdate
from ..templates import TEMPLATES, copy_data, copy_title, default_title, get_template

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    return storage.list_documents()


@router.post("", response_model=Document, status_code=201)
def create_document(payload: DocumentCreate) -> Document:
    if payload.template not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown template")
    data = payload.data or get_template(payload.template).defaults
    title = payload.title or default_title(payload.template, data)
    return storage.create_document(payload.template, payload.style, title, data)


@router.get("/{document_id}", response_model=Document)
def read_document(document_id: str) -> Document:
    doc = storage.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/{document_id}", response_model=Document)
def update_document(document_id: str, payload: DocumentUpdate) -> Document:
    doc = storage.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    # A title follows the client and address until someone renames the document.
    default = default_title(doc.template, doc.data)
    renamed = doc.title not in (default, copy_title(default))
    title = payload.title or (doc.title if renamed else default_title(doc.template, payload.data))
    return storage.save_document(doc, payload.data, title, payload.style)


@router.post("/{document_id}/copy", response_model=Document, status_code=201)
def copy_document(document_id: str) -> Document:
    doc = storage.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return storage.create_document(doc.template, doc.style, copy_title(doc.title), copy_data(doc.data))


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str) -> None:
    if not storage.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
