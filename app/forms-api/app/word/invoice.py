"""The Roofing Job Invoice as an editable Word document.

Every measurement is transcribed from `references/5272_Arezzo_way_invoice.pdf`
in points: `at=` values are the distance from the top of the page to a block's
first line, widths and heights are the ruled boxes. The form began life as a
Word document, so all of it is reachable with Word's own tables, tab stops and
paragraph spacing -- nothing here is positioned absolutely, and editing a
field grows its row the way the original would have.
"""

from __future__ import annotations

from .builder import Sheet
from .kit import Ink, borders, shade, tab_stops, write
from .parts import (
    BULLET_GAP,
    BULLET_LEAD,
    BULLET_MARK,
    BULLET_TEXT,
    COLUMN,
    Caption,
    letterhead,
    party_table,
)

TITLE = 36.7
COMPLIANCE = 57.0
HEAD_RULE = 78.6
LETTERHEAD = 81.8
PARTY = 198.6
#: The party grid's four rules are 24.8pt, 49.2pt and 73.9pt below the first.
PARTY_BOTTOM = PARTY + 73.9
PAY = 280.7
TERMS_RULE = 293.3
BODY_RULE = 301.0
BODY = 316.59
#: The sign-off hangs at the foot of the sheet, not below the last bullet.
THANKS = 700.5
THANKS_UNDERLINE = 726.95
THANKS_RULE = 180.05

#: y, label, field, placeholder -- the four lines under the letterhead.
_META = (
    (151.4, "Invoice #:", "invoice_number", "0000-0000"),
    (163.9, "Date", "invoice_date", "Month, Year"),
    (175.4, "Job ID:", "job_id", "Job ID"),
    (186.9, "Job Location:", "job_location", "Location"),
)

#: Checkbox x, label x, name, label -- all four measured from the page edge.
_PAYMENTS = (
    (36.9, 60.1, "down_payment", "Down Payment"),
    (140.6, 162.8, "progress_payment", "Progress Payment"),
    (249.5, 271.6, "final_payment", "Final Payment"),
)
TERMS_LABEL = 368.6
TERMS_VALUE = 402.1

WARRANTY_TEXT = 36.0
WARRANTY_VALUE = 149.3

#: The summary box, from its ruled edges at 30.6, 168.2, 204.9 and 292.2pt.
#: It follows the scope straight on, with no gap, so it needs no coordinate.
SUM_LABEL = 137.6
SUM_STUB = 36.7
SUM_AMOUNT = 87.3
SUM_HEAD = 23.55
SUM_FIRST = 19.9
SUM_ROW = 12.25
SUM_LAST = 11.75
#: The stub -- a short interior rule the original leaves behind -- divides the
#: label column from the third item row to the last.
STUB_FROM = 2
#: Where the values sit inside their cells.
SUM_INSET = 5.4
SUM_HEAD_DROP = 6.7
SUM_FIRST_DROP = 7.5

_TOTALS = (
    ("subtotal", "SUBTOTAL:", "right"),
    ("scheduled_payment", "SCHEDULED PAYMENT:", "left"),
    ("less_credits", "LESS ANY CREDITS:", "left"),
    ("grand_total", "TOTAL GRAND PRICE", "left"),
)


def build(sheet: Sheet) -> None:
    theme = sheet.theme
    modern = not theme.banners

    title = sheet.para(at=None if modern else TITLE, align="center", size=18)
    sheet.field(title, "doc_title", "Document title",
                ink=Ink(bold=True, size=18, track=theme.tracking or None))

    note = sheet.para(at=None if modern else COMPLIANCE, align="center")
    sheet.field(note, "compliance", "", ink=sheet.ink())

    if theme.banners:
        sheet.rule(at=HEAD_RULE)

    letterhead(sheet, at=LETTERHEAD)
    _meta(sheet)

    party_table(
        sheet,
        at=PARTY,
        gutter=[Caption(13.6, "TO:")],
        name_field="client_name",
        address_label="PROJECT ADDRESS",
        prefix="project",
        # Alone among the values on either form, the invoice's client name is
        # indented past its caption.
        name_inset=9.9,
    )

    _payment_row(sheet)
    _scope(sheet)
    _summary(sheet)
    _closing(sheet)


def _meta(sheet: Sheet) -> None:
    for at, label, name, hint in _META:
        paragraph = sheet.para(at=at if sheet.theme.banners else None,
                               left=COLUMN)
        write(paragraph, f"{label} ", sheet.ink())
        sheet.field(paragraph, name, hint)


def _payment_row(sheet: Sheet) -> None:
    """The three payment-type boxes, then the payment terms over its rule.

    A borderless table rather than one line of tab stops, because the rule
    under the terms stops short of the other three columns and a paragraph
    border would have to run the full width.
    """
    theme = sheet.theme
    right = 612 - theme.margin_x
    edges = [x for x, _, _, _ in _PAYMENTS] + [TERMS_LABEL, TERMS_VALUE, right]
    widths = [b - a for a, b in zip(edges, edges[1:])]

    table = sheet.table(
        widths,
        [TERMS_RULE + 1 - PARTY_BOTTOM],
        at=PARTY_BOTTOM,
        grid=False,
        left=edges[0] - theme.margin_x,
    )
    cells = table.rows[0].cells
    drop = PAY - PARTY_BOTTOM

    for index, (box, label_x, name, label) in enumerate(_PAYMENTS):
        paragraph = sheet.cell_line(cells[index], first=True, before=drop)
        tab_stops(paragraph, (label_x - box, "left"))
        sheet.check(paragraph, name)
        write(paragraph, "\t" + label, sheet.ink())

    write(sheet.cell_line(cells[3], first=True, before=drop), "Terms:",
          sheet.ink())

    terms = sheet.cell_line(cells[4], first=True, before=drop)
    sheet.field(terms, "terms", "Payment terms")
    borders(cells[4], "bottom", color=theme.line)

    sheet.rule(at=BODY_RULE)


def _scope(sheet: Sheet) -> None:
    """The scope of work as a bulleted list, then the warranty line."""
    theme = sheet.theme
    margin = theme.margin_x

    rows = sheet.data.lists.get("scope", [])
    for index in range(len(rows)):
        paragraph = sheet.bullet(
            at=BODY + 0.4 if index == 0 else None,
            before=0 if index == 0 else BULLET_GAP,
            text=BULLET_TEXT - margin,
            marker=BULLET_MARK - margin,
            lead=BULLET_LEAD,
            right=2.8,
        )
        sheet.cell_value(paragraph, "scope", index, "text",
                         "Describe the work\u2026")

    # No gap above this one: the original sets it on the next line down.
    warranty = sheet.para(left=WARRANTY_TEXT - margin, lead=BULLET_LEAD)
    tab_stops(warranty, (WARRANTY_VALUE - margin, "left"))
    sheet.field(warranty, "warranty_prefix", "",
                ink=sheet.ink(color=theme.accent))
    write(warranty, "\t", sheet.ink())
    sheet.field(warranty, "warranty", "e.g. 1 yr workmanship warranty")


def _summary(sheet: Sheet) -> None:
    """The boxed SUMMARY grid: a heading, the item rows, then the totals."""
    theme = sheet.theme
    rows = sheet.data.lists.get("summary", [])

    heights = ([SUM_HEAD, SUM_FIRST] + [SUM_ROW] * (len(rows) - 1)
               + [SUM_ROW] * (len(_TOTALS) - 1) + [SUM_LAST])
    table = sheet.table([SUM_LABEL, SUM_STUB, SUM_AMOUNT], heights)

    head = sheet.emptied(table.cell(0, 0).merge(table.cell(0, 2)))
    sheet.field(sheet.cell_line(head, first=True, before=SUM_HEAD_DROP,
                                size=12, left=SUM_INSET),
                "summary_heading", "SUMMARY", ink=Ink(bold=True, size=12))
    if "surface" in theme.fills:
        shade(head, theme.fills["surface"])

    def money(row: int, drop: float):
        return sheet.cell_line(table.cell(row, 2), first=True, before=drop,
                               left=SUM_INSET)

    for index in range(len(rows)):
        row = 1 + index
        drop = SUM_FIRST_DROP if index == 0 else 0
        right = rows[index].get("align") == "right"
        # The stub only rules the lower item rows; above it the label spans.
        label = table.cell(row, 0)
        if index < STUB_FROM:
            label = sheet.emptied(label.merge(table.cell(row, 1)))
        else:
            borders(table.cell(row, 1), "left", color=theme.line)

        text = sheet.cell_line(
            label, first=True, before=drop,
            align="right" if right else "left",
            left=0 if right else SUM_INSET,
            right=SUM_INSET if right else 0,
        )
        sheet.cell_value(text, "summary", index, "label", "Item")
        sheet.cell_value(money(row, drop), "summary", index, "amount", "$0.00")

    for offset, (name, caption, align) in enumerate(_TOTALS):
        row = 1 + len(rows) + offset
        label = sheet.emptied(table.cell(row, 0).merge(table.cell(row, 1)))
        text = sheet.cell_line(label, first=True, align=align,
                               left=0 if align == "right" else SUM_INSET,
                               right=SUM_INSET if align == "right" else 0)
        write(text, caption, sheet.ink())
        sheet.field(money(row, 0), name, "$0.00", ink=sheet.ink())


def _closing(sheet: Sheet) -> None:
    """The sign-off, which hangs at the foot of the sheet."""
    theme = sheet.theme
    gap = THANKS_UNDERLINE - THANKS - 18 * theme.leading
    if theme.banners:
        # A footer is measured from its foot, which is the underline plus its
        # own weight and the line it is drawn on.
        sheet.footer(THANKS_UNDERLINE + 2)

    closing = sheet.para(align="center", size=18)
    sheet.field(closing, "closing", "Thank You!",
                ink=Ink(italic=True, size=18, font=theme.display))

    inset = (sheet.measure - THANKS_RULE) / 2
    sheet.rule(before=gap, left=inset, right=inset)
