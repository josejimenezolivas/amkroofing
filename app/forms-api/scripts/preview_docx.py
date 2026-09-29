"""Render the Word exports to images so they can be looked at.

`check_docx.py` proves the file is a valid Open XML package containing the
right content. It cannot tell you whether the result looks like a roofing
invoice. This converts each export to PDF with LibreOffice -- an independent
implementation of the format, so it is also a second opinion on whether the
file is readable at all -- and writes a PNG per page.

Needs LibreOffice:  brew install --cask libreoffice

    .venv/bin/python scripts/preview_docx.py invoice
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import word  # noqa: E402
from app.models import WordRequest  # noqa: E402
from app.reference import REFERENCE_AGREEMENT, REFERENCE_INVOICE  # noqa: E402
from app.templates import get_template  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / ".compare"
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

FILLED = {"invoice": REFERENCE_INVOICE, "agreement": REFERENCE_AGREEMENT}


def to_pdf(source: Path, into: Path) -> Path:
    """Convert with LibreOffice, in a throwaway profile so runs don't clash."""
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [SOFFICE, "--headless", f"-env:UserInstallation=file://{profile}",
             "--convert-to", "pdf", "--outdir", str(into), str(source)],
            check=True,
            capture_output=True,
            timeout=180,
        )
    return into / f"{source.stem}.pdf"


def preview(template: str, style: str, blank: bool) -> None:
    data = get_template(template).defaults if blank else FILLED[template]
    name = f"docx-{template}-{style}" + ("-blank" if blank else "")

    source = OUT / f"{name}.docx"
    source.write_bytes(
        word.render_docx(
            WordRequest(template=template, style=style, data=data, filename=name)
        )
    )

    rendered = to_pdf(source, OUT)
    document = pymupdf.open(rendered)
    for number, page in enumerate(document, start=1):
        page.get_pixmap(dpi=110).save(OUT / f"{name}-p{number}.png")
    print(f"  {name}: {document.page_count} pages")
    document.close()
    rendered.unlink()


def main() -> int:
    if not Path(SOFFICE).exists() and not shutil.which("soffice"):
        print("LibreOffice not found; brew install --cask libreoffice")
        return 1

    OUT.mkdir(exist_ok=True)
    for template in sys.argv[1:] or ["invoice", "agreement"]:
        print(template)
        for style in ("classic", "modern"):
            preview(template, style, blank=False)
        preview(template, "classic", blank=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
