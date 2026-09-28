"""Prove the editing affordances do not move the classic layout.

The classic sheets are pixel-matched to the reference PDFs, so an empty form
has to lay out exactly like a filled one -- placeholders, underlines and focus
rings included.

The comparison is the reference document against a copy of itself with every
value cleared, so the only variable is emptiness. Two things must hold:

  * every absolutely positioned element -- the ruled lines, frames, table
    grids, the pieces whose coordinates were copied out of the PDF -- sits in
    exactly the same place;
  * nothing overflows its container, which is how a too-wide placeholder
    announces itself (it wraps a table cell and pushes the row open).

Flow content is allowed to move vertically: a blank form genuinely has shorter
paragraphs than a filled one.

    .venv/bin/python scripts/check_blank_layout.py agreement
"""

import asyncio
import sys

from playwright.async_api import async_playwright

from devapi import APP, copy_of_reference, create, scratch

STRUCTURE = (
    ".rule, .vrule, .sheet__frame, .agr__banner, .letterhead__logo, "
    ".letterhead__name, .letterhead__line, .letterhead__email, "
    ".party__label, .inv__pay-label, .agr__proj-label, .agr__proj-value"
)

MEASURE = f"""
() => {{
  const anchored = [];
  const overflowing = [];

  document.querySelectorAll('.document .sheet').forEach((sheet, page) => {{
    const origin = sheet.getBoundingClientRect();
    const at = (el) => {{
      const r = el.getBoundingClientRect();
      return [r.left - origin.left, r.top - origin.top, r.width, r.height]
        .map((n) => Math.round(n * 100) / 100);
    }};

    sheet.querySelectorAll('{STRUCTURE}').forEach((el, i) => {{
      anchored.push([`p${{page + 1}} ${{el.className.split(' ')[0]}} #${{i}}`, at(el)]);
    }});

    // A cell whose content is wider than the cell itself has wrapped.
    sheet.querySelectorAll('.ed').forEach((el) => {{
      const parent = el.parentElement;
      if (!parent) return;
      const a = el.getBoundingClientRect();
      const b = parent.getBoundingClientRect();
      if (a.right > b.right + 0.5 || a.bottom > b.bottom + 0.5) {{
        overflowing.push([
          `p${{page + 1}} ${{parent.className.split(' ')[0]}} / ${{el.dataset.placeholder ?? ''}}`,
          Math.round((a.right - b.right) * 100) / 100,
          Math.round((a.bottom - b.bottom) * 100) / 100,
        ]);
      }}
    }});
  }});

  return {{ anchored, overflowing }};
}}
"""


def blanked(data: dict) -> dict:
    """The same document with every value removed but its shape intact."""
    return {
        "fields": {k: "" for k in data["fields"]},
        "checks": {k: False for k in data["checks"]},
        "lists": {
            name: [{k: ("" if k != "style" else v) for k, v in row.items()} for row in rows]
            for name, rows in data["lists"].items()
        },
        "signatures": {},
        "images": {},
    }


async def run(template: str) -> int:
    filled = copy_of_reference(template)
    empty = create(template, "classic", blanked(filled["data"]))

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(APP, wait_until="networkidle")

        measured = []
        for doc in (filled, empty):
            await page.get_by_text(doc["title"], exact=False).first.click()
            await page.wait_for_selector(".document .sheet")
            await page.wait_for_timeout(400)
            measured.append(await page.evaluate(MEASURE))

        await browser.close()

    return report(template, *measured)


def report(template: str, filled: dict, empty: dict) -> int:
    # Only position matters. A container that shrink-wraps its own text is
    # naturally narrower when that text is gone, which moves nothing.
    moved = [
        (key, box, other)
        for (key, box), (_, other) in zip(filled["anchored"], empty["anchored"])
        if any(abs(a - b) > 0.01 for a, b in zip(box[:2], other[:2]))
    ]
    overflow = empty["overflowing"]

    print(f"{template}: {len(filled['anchored'])} anchored elements")
    for key, box, other in moved[:15]:
        print(f"  MOVED {key}: {box} -> {other}")
    for key, right, bottom in overflow[:15]:
        print(f"  OVERFLOW {key}: right +{right}, bottom +{bottom}")

    if moved or overflow:
        print(f"  {len(moved)} moved, {len(overflow)} overflowing")
    else:
        print("  nothing moved, nothing overflows")
    return len(moved) + len(overflow)


if __name__ == "__main__":
    failures = 0
    for name in sys.argv[1:] or ["invoice", "agreement"]:
        with scratch():
            failures += asyncio.run(run(name))
    sys.exit(1 if failures else 0)
