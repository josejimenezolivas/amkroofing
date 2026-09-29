"""Export the modern layouts through the real UI and render them as images.

Same path a user takes: create the document, switch to Modern, hit Export.
The scratch document is removed afterwards.

    .venv/bin/python scripts/preview_modern.py agreement
"""

import asyncio
import sys
from pathlib import Path

import pymupdf
from playwright.async_api import async_playwright

from devapi import APP, copy_of_reference, scratch, signed_in_page

OUT = Path(__file__).resolve().parents[1] / ".compare"


async def run(template: str) -> None:
    OUT.mkdir(exist_ok=True)
    doc = copy_of_reference(template, style="modern")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await signed_in_page(browser, accept_downloads=True)
        await page.goto(APP, wait_until="networkidle")

        await page.get_by_text(doc["title"], exact=False).first.click()
        await page.wait_for_selector(".document .msheet")

        await page.get_by_role("button", name="Export").click()
        async with page.expect_download() as pending:
            await page.get_by_role("menuitem", name="PDF document").click()
        pdf_path = OUT / f"modern-{template}.pdf"
        await (await pending.value).save_as(pdf_path)
        await browser.close()

    doc = pymupdf.open(pdf_path)
    print(f"{template}: {doc.page_count} pages")
    for i, page_obj in enumerate(doc, start=1):
        page_obj.get_pixmap(dpi=110).save(OUT / f"modern-{template}-p{i}.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["invoice", "agreement"]:
        with scratch():
            asyncio.run(run(name))
