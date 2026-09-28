"""HTML -> PDF using headless Chromium.

The browser prints the exact markup the user was just editing, so the download
is guaranteed to match the screen rather than being a second, drifting
re-implementation of the layout.
"""

from contextlib import asynccontextmanager

from playwright.async_api import Browser, async_playwright

from .models import RenderRequest

_playwright = None
_browser: Browser | None = None


async def startup() -> None:
    global _playwright, _browser
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch()


async def shutdown() -> None:
    global _playwright, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None


@asynccontextmanager
async def lifespan_browser():
    await startup()
    try:
        yield
    finally:
        await shutdown()


def build_page(req: RenderRequest, base_url: str | None) -> str:
    base_tag = f'<base href="{base_url}">' if base_url else ""
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
{base_tag}
<style>{req.css}</style>
<style>
  /* The printed sheet is the page: no browser margins, no editor chrome. */
  @page {{ size: letter; margin: {req.margin_top} {req.margin_side} {req.margin_bottom}; }}
  html, body {{ margin: 0; padding: 0; background: #fff; }}
</style>
</head>
<body class="print-root">{req.html}</body>
</html>"""


async def render_pdf(req: RenderRequest, base_url: str | None = None) -> bytes:
    if _browser is None:
        raise RuntimeError("Browser is not running")

    page = await _browser.new_page()
    try:
        await page.set_content(build_page(req, base_url), wait_until="load")
        await page.evaluate("document.fonts.ready")
        return await page.pdf(
            format="Letter",
            print_background=True,
            prefer_css_page_size=True,
            margin={
                "top": req.margin_top,
                "right": req.margin_side,
                "bottom": req.margin_bottom,
                "left": req.margin_side,
            },
        )
    finally:
        await page.close()
