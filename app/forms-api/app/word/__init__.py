"""Word export.

The PDF is printed from the browser, so it matches the screen exactly. Word
is a different job: the file has to keep working as a document after it is
opened, so it is built here from the same data through Word's own constructs
-- tables, lists, paragraphs, content controls -- rather than converted from
the page's HTML. Editing an address in Word grows its row, and the rest of
the form moves out of the way, because nothing is pinned to a coordinate.
"""

from __future__ import annotations

from io import BytesIO

from ..models import WordRequest
from . import agreement, invoice
from .builder import Sheet
from .kit import THEMES

_TEMPLATES = {"invoice": invoice.build, "agreement": agreement.build}


def render_docx(request: WordRequest) -> bytes:
    sheet = Sheet(request.data, THEMES[request.style])
    _TEMPLATES[request.template](sheet)

    buffer = BytesIO()
    sheet.document.save(buffer)
    return buffer.getvalue()
