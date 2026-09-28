"""Blocks the invoice and the agreement both use.

The coordinates are the reference PDFs' own, in points from the page edge.
"""

from __future__ import annotations

from typing import NamedTuple

from .builder import Sheet
from .kit import Ink, TOP, write


class Caption(NamedTuple):
    """A line in the ruled grid's left gutter.

    `drop` is measured from the grid's first rule and `left` from the page
    edge; without a `left` the line is centred in the gutter, which is how
    the invoice sets its "TO:".
    """

    drop: float
    text: str
    left: float | None = None
    ink: Ink | None = None

#: Where the body text sits: 36pt in, 5.4pt inside the 30.6pt text margin.
COLUMN = 5.4

#: The scope list, shared by both forms: the bullet at 54pt, its text at 72pt,
#: on 11.5pt lines with 2.7pt between items.
BULLET_MARK = 54.0
BULLET_TEXT = 72.0
BULLET_LEAD = 11.5
BULLET_GAP = 2.7

#: The logo, 108 x 51pt, starting 3.8pt above the company name's first line.
LOGO_TOP = 3.8
LOGO_WIDTH = 108.0
LOGO_HEIGHT = 51.0

#: The centred company block. The original's own box is 220.9pt to 432.5pt,
#: but its phone line fills that to the point and overflows it on the page,
#: which a Word cell would wrap instead -- so the column is given room to
#: spare and the block is held in place by its centre.
BLOCK_CENTRE = 326.7
BLOCK_WIDTH = 250.0
NAME_SIZE = 14.0

#: Each following line of the company block, as an offset from the one above.
BLOCK_STEP = (18.6, 12.5, 12.5, 12.5)
#: The email sits below the logo rather than in the centred block.
EMAIL_TOP = 51.0
LETTERHEAD_HEIGHT = 71.0


def letterhead(sheet: Sheet, *, at: float | None = None,
               logo_left: float = 35.0) -> None:
    """The logo, the centred company block, and the email beneath the logo.

    Laid out as a borderless three-column table so the logo and the company
    details sit side by side and stay that way when either is edited. `at` is
    the top of the company name, which the logo overhangs slightly; without
    it the block simply follows whatever came before.
    """
    theme = sheet.theme
    gutter = BLOCK_CENTRE - BLOCK_WIDTH / 2 - theme.margin_x
    tail = sheet.measure - gutter - BLOCK_WIDTH

    # The logo overhangs the rule above it by a fraction of a point, which the
    # flow cannot do, so the block starts at whichever is lower.
    top = sheet.cursor if at is None else max(sheet.cursor, at - LOGO_TOP)
    drop = LOGO_TOP if at is None else at - top

    table = sheet.table(
        [gutter, BLOCK_WIDTH, tail],
        [LETTERHEAD_HEIGHT],
        at=top,
        grid=False,
    )
    left, middle, _ = table.rows[0].cells
    left.vertical_alignment = TOP
    middle.vertical_alignment = TOP

    # An image cannot go in a pinned line box -- an exact leading would crop
    # it -- so the logo's line is allowed to grow to the picture's height.
    sheet.logo(
        sheet.cell_line(left, first=True, left=logo_left - theme.margin_x,
                        lead=LOGO_HEIGHT, rule="atLeast"),
        width=LOGO_WIDTH,
        height=LOGO_HEIGHT,
    )

    email = sheet.cell_line(left, left=COLUMN,
                            before=drop + EMAIL_TOP - LOGO_HEIGHT)
    sheet.field(
        email,
        "company_email",
        "email@example.com",
        ink=sheet.ink(color=theme.accent, underline=theme.banners),
    )

    name = sheet.cell_line(middle, first=True, before=drop, align="center",
                           size=NAME_SIZE)
    sheet.field(
        name,
        "company_name",
        "Company name",
        ink=Ink(bold=True, size=NAME_SIZE, color=theme.accent,
                track=theme.tracking or None),
    )

    licence = sheet.cell_line(middle, align="center",
                              before=BLOCK_STEP[0] - theme.lead(NAME_SIZE))
    write(licence, "License ", sheet.ink(bold=True))
    sheet.field(licence, "company_license", "", ink=sheet.ink(bold=True))

    gap = BLOCK_STEP[1] - theme.lead(theme.size)
    for field_name in ("company_street", "company_city"):
        sheet.field(
            sheet.cell_line(middle, align="center", before=gap),
            field_name,
            "",
            ink=sheet.ink(),
        )

    # The phone and cell fill the block to within a point, so this line must
    # not wrap: one space between them, and no letter-spacing.
    contact = sheet.cell_line(middle, align="center", before=gap)
    sheet.field(contact, "company_phone", "", ink=sheet.ink(bold=True))
    write(contact, " ", sheet.ink(bold=True))
    sheet.field(contact, "company_cell", "", ink=sheet.ink(bold=True))


#: The ruled grid's column edges, from the page edge: gutter, then street,
#: city, state/ZIP and phone.
_EDGES = (30.6, 90.8, 339.1, 450.0, 508.5, 581.4)
#: The three rows, measured between the grid's four rules.
_ROWS = (24.8, 24.4, 24.7)
#: Captions sit 5.4pt in from their cell's rule and 2.2pt below the row's.
_INSET = 5.4
_DROP = 2.2

_PARTS = ("address", "city", "state_zip", "phone")


def party_table(
    sheet: Sheet,
    *,
    at: float | None = None,
    gutter: list[Caption],
    name_field: str,
    address_label: str,
    prefix: str,
    name_placeholder: str = "Client name",
    name_inset: float = _INSET,
) -> None:
    """The boxed NAME / ADDRESS / ALTERNATE ADDRESS grid.

    Three rows: a full-width name, then the address and the alternate address
    each split into street, city, state/ZIP and phone. The left gutter is one
    cell merged down the height of the box, carrying the "TO:" or
    "BUYER/OWNER" caption at its measured offsets.
    """
    theme = sheet.theme
    widths = [b - a for a, b in zip(_EDGES, _EDGES[1:])]
    table = sheet.table(widths, list(_ROWS), at=at,
                        left=_EDGES[0] - theme.margin_x)

    caption = sheet.emptied(table.cell(0, 0).merge(table.cell(2, 0)))
    caption.vertical_alignment = TOP
    above = 0.0
    for index, entry in enumerate(gutter):
        ink = entry.ink or sheet.ink(bold=True)
        line = sheet.cell_line(
            caption,
            first=index == 0,
            before=entry.drop - above,
            size=ink.size,
            align="center" if entry.left is None else "left",
            left=0 if entry.left is None else entry.left - _EDGES[0],
        )
        write(line, entry.text, ink)
        above = entry.drop + theme.lead(ink.size or theme.size)

    name_cell = sheet.emptied(table.cell(0, 1).merge(table.cell(0, 4)))
    sheet.label(sheet.cell_line(name_cell, first=True, before=_DROP,
                                left=_INSET, size=theme.small), "NAME")
    sheet.field(sheet.cell_line(name_cell, left=name_inset), name_field,
                name_placeholder)

    rows = (
        (1, address_label, prefix,
         ("Street address", "City", "State/ZIP", "Phone")),
        (2, "ALTERNATE ADDRESS (IF ANY)", "alt",
         ("Alternate address", "City", "State/ZIP", "Phone")),
    )

    for index, label, field_prefix, hints in rows:
        captions = (label, "CITY", "STATE/ZIP", "PHONE")
        for column, (caption_text, part, hint) in enumerate(
            zip(captions, _PARTS, hints), start=1
        ):
            value = sheet.stacked(table.cell(index, column), caption_text,
                                  before=_DROP, left=_INSET)
            sheet.field(value, f"{field_prefix}_{part}", hint)
