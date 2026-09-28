from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

TemplateId = Literal["invoice", "agreement"]

#: "classic" reproduces the reference PDF exactly; "modern" is a redesign of the
#: same data. Both read and write the same `DocumentData`.
DocStyle = Literal["classic", "modern"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentData(BaseModel):
    """Everything a user can change on a form.

    `fields` holds single-line text, `checks` holds checkbox state, `lists` holds
    repeatable rows (scope bullets, summary lines, allowance rows),
    `signatures` holds PNG data URLs drawn in the browser and `images` holds
    uploaded artwork such as a replacement logo.
    """

    fields: dict[str, str] = Field(default_factory=dict)
    checks: dict[str, bool] = Field(default_factory=dict)
    lists: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    signatures: dict[str, str] = Field(default_factory=dict)
    images: dict[str, str] = Field(default_factory=dict)


class DocumentSummary(BaseModel):
    id: str
    template: TemplateId
    style: DocStyle = "classic"
    title: str
    created_at: datetime
    updated_at: datetime


class Document(DocumentSummary):
    data: DocumentData = Field(default_factory=DocumentData)


class DocumentCreate(BaseModel):
    template: TemplateId
    style: DocStyle = "classic"
    title: str | None = None
    data: DocumentData | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    style: DocStyle | None = None
    data: DocumentData


class TemplateInfo(BaseModel):
    id: TemplateId
    name: str
    description: str
    pages: int
    defaults: DocumentData


class WordRequest(BaseModel):
    """A Word export.

    Unlike the PDF, which prints the page's own markup, this is built from the
    data so the result is a document Word can keep editing.
    """

    template: TemplateId
    style: DocStyle = "classic"
    filename: str = "document"
    data: DocumentData


class RenderRequest(BaseModel):
    """A serialized snapshot of the on-screen document, printed verbatim."""

    html: str
    css: str = ""
    filename: str = "document"
    #: `@page` margins. Fixed-position layouts print at "0" and paint their own
    #: margins; flowing layouts need real page margins so every page gets them.
    #: Chromium's PDF API only accepts px, in, cm and mm here -- not pt.
    margin_top: str = "0"
    margin_bottom: str = "0"
    margin_side: str = "0"
