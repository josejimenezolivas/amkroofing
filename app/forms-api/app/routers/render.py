import re

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from .. import word
from ..config import PDF_SERVICE_URL
from ..models import RenderRequest, WordRequest

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

router = APIRouter(prefix="/api/render", tags=["render"])


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", name).strip() or "document"
    return cleaned[:120]


@router.post("/pdf")
async def render_pdf(payload: RenderRequest, request: Request) -> Response:
    """Print the on-screen markup with headless Chromium.

    Chromium lives in its own service so nothing else here waits for it to
    start. That service has no public route; this handler, behind sign-in, is
    the only way in.
    """
    origin = request.headers.get("origin")
    job = {**payload.model_dump(), "base_url": f"{origin}/" if origin else None}
    try:
        async with httpx.AsyncClient(timeout=55) as client:
            res = await client.post(f"{PDF_SERVICE_URL.rstrip('/')}/render", json=job)
        res.raise_for_status()
    except httpx.HTTPError as err:
        raise HTTPException(status_code=502, detail="The PDF could not be made. Try again.") from err

    filename = f"{_safe_filename(payload.filename)}.pdf"
    return Response(
        content=res.content,
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
