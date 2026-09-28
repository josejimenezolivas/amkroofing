"""Diff the Word export against the original PDFs in `references/`.

The classic forms began life as Word documents, so the geometry in them is
reachable with Word's own layout model -- the numbers just have to be right.
This renders the export through LibreOffice and overlays it on the original,
the same way `compare_to_reference.py` does for the browser's PDF, so the
Word layout can be tuned against a number instead of an impression.

Needs LibreOffice:  brew install --cask libreoffice

    .venv/bin/python scripts/compare_docx_to_reference.py invoice
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import word  # noqa: E402
from app.models import WordRequest  # noqa: E402
from app.reference import REFERENCE_AGREEMENT, REFERENCE_INVOICE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".compare"
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

REFERENCES = {
    "invoice": ROOT.parent / "references" / "5272_Arezzo_way_invoice.pdf",
    "agreement": ROOT.parent / "references" / "3360_Ramona_Palo_Alto_sample_4.pdf",
}
DATA = {"invoice": REFERENCE_INVOICE, "agreement": REFERENCE_AGREEMENT}

DPI = 150


def render(template: str) -> Path:
    source = OUT / f"cmp-{template}.docx"
    source.write_bytes(
        word.render_docx(
            WordRequest(template=template, style="classic", data=DATA[template],
                        filename=template)
        )
    )
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [SOFFICE, "--headless", f"-env:UserInstallation=file://{profile}",
             "--convert-to", "pdf", "--outdir", str(OUT), str(source)],
            check=True, capture_output=True, timeout=180,
        )
    return OUT / f"cmp-{template}.pdf"


def gray(page) -> np.ndarray:
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)


def bands(a: np.ndarray, b: np.ndarray, rows: int = 12) -> list[str]:
    """Where on the page the two disagree, as a coarse vertical profile.

    A single page-wide average hides the fact that the top half is perfect and
    one table below it is 8pt low, which is exactly what needs finding.
    """
    height = a.shape[0] // rows
    out = []
    for index in range(rows):
        top, bottom = index * height, (index + 1) * height
        drift = np.mean(np.abs(a[top:bottom].astype(int) - b[top:bottom].astype(int)))
        out.append(f"{index * 100 // rows:>3}% {drift:5.1f}")
    return out


def compare(template: str) -> None:
    mine = pymupdf.open(render(template))
    reference = pymupdf.open(REFERENCES[template])
    print(f"{template}: word {mine.page_count} pages, reference {reference.page_count}")

    for index in range(min(mine.page_count, reference.page_count)):
        a, b = gray(reference[index]), gray(mine[index])
        rows = min(a.shape[0], b.shape[0])
        columns = min(a.shape[1], b.shape[1])
        a, b = a[:rows, :columns], b[:rows, :columns]

        # Reference red, export blue, multiplied: agreement goes black.
        stacked = np.stack([b, np.minimum(a, b), a], axis=-1).astype(np.uint8)
        Image.fromarray(stacked).save(OUT / f"cmp-{template}-p{index + 1}.png")

        drift = np.mean(np.abs(a.astype(int) - b.astype(int)))
        print(f"  page {index + 1}: {drift:5.2f}/255   " + "  ".join(bands(a, b)))


def main() -> int:
    if not Path(SOFFICE).exists():
        print("LibreOffice not found; brew install --cask libreoffice")
        return 1
    OUT.mkdir(exist_ok=True)
    for template in sys.argv[1:] or ["invoice", "agreement"]:
        compare(template)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
