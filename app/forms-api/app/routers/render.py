import re

from fastapi import APIRouter, Request
from fastapi.responses import Response

from .. import pdf, word
from ..models import RenderRequest, WordRequest

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

router = APIRouter(prefix="/api/render", tags=["render"])


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", name).strip() or "document"
    return cleaned[:120]


@router.post("/pdf")
async def render_pdf(payload: RenderRequest, request: Request) -> Response:
    origin = request.headers.get("origin")
    base_url = f"{origin}/" if origin else None
    data = await pdf.render_pdf(payload, base_url=base_url)
    filename = f"{_safe_filename(payload.filename)}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/docx")
def render_docx(payload: WordRequest) -> Response:
    """Build a Word document from the data, not from the page's markup.

    The PDF prints what is on screen. Word has to stay editable afterwards, so
    it is composed out of Word's own tables and paragraphs instead.
    """
    data = word.render_docx(payload)
    filename = f"{_safe_filename(payload.filename)}.docx"
    return Response(
        content=data,
        media_type=DOCX,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
