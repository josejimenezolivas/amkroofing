"""Dev tool: render a document through the real export path and diff it
against the original PDF in `references/`.

Writes side-by-side and difference images to `server/.compare/`. Requires the
API on :8000 and the Vite dev server on :5173.

    .venv/bin/python scripts/compare_to_reference.py invoice
"""

import asyncio
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image
from playwright.async_api import async_playwright

from devapi import API, APP, copy_of_reference, http, scratch, signed_in_page

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".compare"
REFERENCES = {
    "invoice": ROOT.parent / "references" / "5272_Arezzo_way_invoice.pdf",
    "agreement": ROOT.parent / "references" / "3360_Ramona_Palo_Alto_sample_4.pdf",
}

COLLECT = """
() => {
  const css = [];
  for (const sheet of document.styleSheets) {
    try { for (const rule of sheet.cssRules) css.push(rule.cssText); } catch {}
  }
  const root = document.querySelector('.document');
  return { html: root.outerHTML, css: css.join('\\n') };
}
"""


async def build_pdf(template: str) -> bytes:
    with scratch():
        doc = copy_of_reference(template)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await signed_in_page(browser, viewport={"width": 1600, "height": 1200})
            await page.goto(APP, wait_until="networkidle")
            await page.get_by_text(doc["title"], exact=False).first.click()
            await page.wait_for_selector(".document .sheet")
            await page.wait_for_timeout(700)
            payload = await page.evaluate(COLLECT)
            await browser.close()

        payload["filename"] = template
        res = http.post(f"{API}/api/render/pdf", json=payload, timeout=120)
        res.raise_for_status()
        return res.content


def write_comparison(template: str, pdf_bytes: bytes) -> None:
    OUT.mkdir(exist_ok=True)
    mine_path = OUT / f"{template}.pdf"
    mine_path.write_bytes(pdf_bytes)

    mine = pymupdf.open(mine_path)
    ref = pymupdf.open(REFERENCES[template])
    print(f"{template}: rendered {mine.page_count} pages, reference has {ref.page_count}")

    for i in range(max(mine.page_count, ref.page_count)):
        pages = [doc[i] if i < doc.page_count else None for doc in (ref, mine)]
        if pages[0] is None or pages[1] is None:
            print(f"  page {i + 1}: only one side has this page")
            continue

        # Tint the reference red and the render blue and multiply them: shared
        # ink turns near-black, anything misplaced stays coloured.
        a, b = (numpy_gray(p) for p in pages)
        h = min(a.shape[0], b.shape[0])
        w = min(a.shape[1], b.shape[1])
        a, b = a[:h, :w], b[:h, :w]

        rgb = np.stack([b, np.minimum(a, b), a], axis=-1).astype(np.uint8)
        Image.fromarray(rgb).save(OUT / f"{template}-p{i + 1}-overlay.png")

        drift = np.mean(np.abs(a.astype(int) - b.astype(int)))
        print(f"  page {i + 1}: mean ink difference {drift:.2f}/255")

    print(f"wrote {OUT}")


def numpy_gray(page) -> "np.ndarray":
    pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)


async def main() -> None:
    for template in sys.argv[1:] or ["invoice", "agreement"]:
        write_comparison(template, await build_pdf(template))


if __name__ == "__main__":
    asyncio.run(main())
