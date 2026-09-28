"""Report how far each part of the Word export sits from the original.

The overlay from `compare_docx_to_reference.py` shows *that* something is out
of place. This says by how much and in which direction, in points, by finding
the same piece of text in both PDFs and subtracting its position -- which is
what you need to correct a number in the layout.

Needs LibreOffice:  brew install --cask libreoffice

    .venv/bin/python scripts/measure_docx.py invoice
"""

import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compare_docx_to_reference import REFERENCES, render  # noqa: E402

#: Text to line up, in reading order, keyed by template and printed page.
ANCHORS = {
    "invoice 1": [
        "ROOFING JOB INVOICE",
        "This form complies",
        "AMK ROOFING",
        "License",
        "184 TALMADGE AVE",
        "SAN JOSE CA 95127",
        "PHONE/FAX",
        "amkroofing@amkroofing.com",
        "Invoice #",
        "Date",
        "Job ID",
        "Job Location",
        "TO:",
        "NAME",
        "Jeff Westererine",
        "PROJECT ADDRESS",
        "5272 Arezzo way",
        "ALTERNATE ADDRESS",
        "Down Payment",
        "Progress Payment",
        "Final Payment",
        "Terms:",
        "hereby propose",
        "Extra work we perform",
        "SUMMARY",
        "Replace broken tile",
        "SUBTOTAL:",
        "TOTAL GRAND PRICE",
        "Thank You!",
    ],
    "agreement 1": [
        "RESIDENTIAL ROOFING",
        "AGREEMENT",
        "This form complies",
        "This document, including",
        "THIS AGREEMENT IS BETWEEN",
        "AMK ROOFING",
        "THIS AGREEMENT IS ENTERED INTO",
        "BUYER/",
        "NAME",
        "Michaeal",
        "ADDRESS",
        "3360 Ramona st",
        "Hereinafter called",
        "ROOFING PROJECT",
        "PROJECT ADDRESS - STREET",
        "ZIP CODE",
        "Also Known as Legal",
        "Recorded in Book",
        "DESCRIPTION OF THE ROOFING",
        "Check here if this space",
        "NOT INCLUDED:",
        "ALLOWANCES:",
        "ADDITIONAL ALLOWANCES NOTES",
    ],
    "agreement 2": [
        "TIME FOR STARTING",
        "CONTRACT PRICE",
        "PAYMENT:",
        "Down Payment:",
        "THE DOWN PAYMENT MAY NOT",
        "The Schedule of Progress",
        "The schedule of progress",
        "Upon satisfactory payment",
        "All payments will be made",
        "IT IS AGAINST THE LAW",
        "The buyer may not require",
        "Contractor or Owner prior",
        "Do not sign this agreement",
    ],
    "agreement 3": [
        "owner cancels this agreement",
        "TERMS AND CONDITIONS",
        "The terms and conditions",
        "NOTICE",
        "Contractors are required",
        "You, as Owner or Tenant",
        "List of Documents",
        "You are entitled to a",
        "Unless the customer initiated",
        "THIS AGREEMENT CONSISTS OF",
        "OWNER",
        "CONTRACTOR SIGNATURE",
    ],
}


def lines(page):
    """Every typeset line, in reading order, with its characters.

    `page.search_for` is case-insensitive and returns hits in no useful
    order, which is how "NAME" ends up reported at the position of "Company
    name". Reading the characters is exact on both counts.
    """
    found = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            characters = [c for span in line["spans"] for c in span["chars"]]
            found.append((line["bbox"][1], characters))
    return sorted(found, key=lambda line: line[0])


def anchor_boxes(page, needles: list[str]) -> dict[str, tuple[float, float]]:
    """Top-left corner of the first occurrence of each needle, in points."""
    typeset = lines(page)
    found = {}
    for needle in needles:
        for top, characters in typeset:
            at = "".join(c["c"] for c in characters).find(needle)
            if at != -1:
                found[needle] = (round(characters[at]["bbox"][0], 1),
                                 round(top, 1))
                break
    return found


def report(template: str, page: int) -> None:
    needles = ANCHORS[f"{template} {page}"]
    mine = pymupdf.open(render(template))
    reference = pymupdf.open(REFERENCES[template])

    a = anchor_boxes(reference[page - 1], needles)
    b = anchor_boxes(mine[page - 1], needles)

    print(f"{template} page {page}"
          "  (reference -> word, points; + means too far right/down)")
    print(f"  {'anchor':32} {'ref x,y':>14}  {'word x,y':>14}   {'dx':>6} {'dy':>6}")

    worst = 0.0
    for needle in needles:
        if needle not in a:
            print(f"  {needle[:32]:32} {'not in reference':>14}")
            continue
        if needle not in b:
            print(f"  {needle[:32]:32} {str(a[needle]):>14}  {'MISSING':>14}")
            continue
        dx = b[needle][0] - a[needle][0]
        dy = b[needle][1] - a[needle][1]
        worst = max(worst, abs(dx), abs(dy))
        flag = "" if max(abs(dx), abs(dy)) < 2 else "  <--"
        print(f"  {needle[:32]:32} {str(a[needle]):>14}  {str(b[needle]):>14}   "
              f"{dx:+6.1f} {dy:+6.1f}{flag}")

    print(f"  worst offset: {worst:.1f}pt")


def main() -> int:
    wanted = sys.argv[1:]
    for key in ANCHORS:
        template, page = key.rsplit(" ", 1)
        if not wanted or template in wanted or key in wanted:
            report(template, int(page))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
