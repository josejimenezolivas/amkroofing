"""The agreement's standing text, loaded for the Word export.

Neither of these is authored here. The legal wording is the same JSON the
browser renders, and the terms are the typeset lines extracted from the
reference PDF by `scripts/generate_terms.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .. import config


@lru_cache(maxsize=1)
def legal() -> dict[str, str | list[str]]:
    return json.loads(config.LEGAL_PROSE.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Block:
    heading: bool
    text: str


@lru_cache(maxsize=1)
def terms() -> list[Block]:
    """Reflow the terms pages back into paragraphs.

    The stored lines carry the original's line breaks so the classic pages can
    reproduce them exactly. Word sets its own measure and needs paragraphs
    instead. A justified line is by definition not the last of its paragraph,
    which is the only structure needed to stitch them back together.
    """
    blocks: list[Block] = []
    buffer: list[str] = []

    for sheet in json.loads(config.TERMS_LINES.read_text(encoding="utf-8")):
        for column in sheet["columns"]:
            for line in column:
                buffer.append(line["t"].strip())
                if line["j"]:
                    continue

                text = " ".join(buffer)
                text = " ".join(text.split())
                buffer = []
                if not text:
                    continue
                # Headings are the short, fully capitalised standalone lines.
                blocks.append(
                    Block(heading=len(text) <= 55 and text == text.upper(), text=text)
                )

    return blocks
