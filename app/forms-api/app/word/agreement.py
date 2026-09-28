"""The Residential Roofing Agreement as an editable Word document.

Seven printed pages: the job details, the payment terms, the signatures, and
then the standing terms and conditions, which the original sets in two
columns and this keeps in two columns using a real Word section.
"""

from __future__ import annotations

from docx.shared import Pt

from .builder import LETTER, Sheet
from .kit import (
    Ink,
    RULE,
    TOP,
    borders,
    cell_margins,
    copy_page_setup,
    fixed_widths,
    keep_with_next,
    page_number,
    row_height,
    spacing,
    tab_stops,
    table_indent,
    two_column_section,
    write,
)
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
from .prose import legal, terms

#: Page 1, in points from the page edge, off the reference PDF.
MASTHEAD = 36.7
MASTHEAD_LEAD = 20.7
MASTHEAD_WIDTH = 329.6
COMPLIANCE = 88.0
INTRO = 39.4
INTRO_LEFT = 365.4
INTRO_WIDTH = 211.6
INTRO_LEAD = 11.5
BETWEEN = (108.0, 115.8, 130.0)
LETTERHEAD = 133.2
LOGO_LEFT = 37.5
ENTERED = 201.9
ENTERED_LEAD = 11.4
PARTY = 225.0
HEREINAFTER = 301.2
HEREINAFTER_LEFT = 38.8
PROJECT = (312.3, 314.3, 326.5)
#: The project address strip: its cell edges, then its label and value lines.
PROJECT_EDGES = (30.6, 274.5, 364.5, 486.0, 581.4)
PROJECT_LABEL = 329.3
PROJECT_VALUE = 339.7
PROJECT_STREET_INSET = 15.4
LEGAL_RULE = 352.3
LEGAL_TOP = 358.8
LEGAL_LEAD = 11.5
BODY_RULE = 388.3
BODY = 397.09
#: Body blocks, as the gap each leaves above itself and the line it sets on.
WARRANTY = (1.9, 11.5)
WARRANTY_VALUE = 149.3
CHECKS = (10.9, 13.0)
CHECKS_SECOND = (1.5, 10.3)
CHECK_BOX = 36.9
CHECK_TEXT = 61.7
SCOPE_RULE = 6.2
NOT_INCLUDED = (2.6, 11.4)
ALLOWANCES = (15.7, 11.45)
NOTES = 2.0
#: Page 2. The standing clauses are 10pt on 11.5pt lines, except the ones the
#: original shouts in 12pt bold on 13.8pt lines.
PAY_RULE = 47.5
PAY_TIMING = 58.5
PRICE = (148.3, 152.2, 165.3)
PAY_BODY = 175.1
PROSE_LEAD = 11.5
LOUD_LEAD = 13.8

#: Page 3.
SIGN_TOP = 36.4
SIGN_BANNER = (70.5, 74.3, 87.5)
SIGN_BODY = 91.3
#: The box the owner initials to acknowledge the right to cancel, 18.2pt
#: square against the right margin beside the clause it belongs to.
CANCEL_BOX = 544.0
CANCEL_SIZE = 18.2

#: Pages 4-7: the title page, then the two columns of terms.
TERMS_TITLE = 34.3
TERMS_TOP = 35.83
#: The columns run 36pt to 299.1pt and 315pt to 577.7pt.
TERMS_EDGES = (36.0, 577.7)
TERMS_GUTTER = 15.9
TERMS_LEAD = 10.3
TERMS_GAP = 4.5
TERMS_HEADING = 4.55
#: The last line of a column clears the initials strip at the foot.
TERMS_FOOT = 730.0

#: The strip at the foot of every page: a ruled blank for each party's
#: initials and the date beside it, captioned underneath. The rules run
#: 398.2-427.7, 434.5-455.9, 467.1-496.6 and 503.4-524.8pt from the page edge.
FOOT_BLANKS = ((398.2, 427.7), (434.5, 455.9), (467.1, 496.6), (503.4, 524.8))
FOOT_CAPTIONS = ("Initials", "Date", "Initials", "Date")
#: The rules are 739.6pt down, the captions 2.6pt under them and 2.25pt in,
#: and the page number a little lower again.
FOOT_RULE = 1.0
FOOT_DROP = 2.6
FOOT_PAGE_DROP = 6.35
FOOT_CAPTION = 16.35
FOOT_CAPTION_INSET = 2.25
#: The strip's bottom edge. Page one's sits higher and carries no number, so
#: the difference between the two is more than it looks.
FOOT_BOTTOM = 755.9
FOOT_FIRST_RISE = 11.2
#: The terms pages name themselves at the foot. Page one is not numbered.
FOOT_TITLE = "Terms and Conditions"

#: Description, amount -- the allowances grid repeats this pair three times.
_ALLOWANCE_PAIRS = (("desc1", "amt1"), ("desc2", "amt2"), ("desc3", "amt3"))
#: The allowances grid's six columns and its 12pt rows.
_ALLOWANCE_WIDTHS = (131.7, 49.1, 131.7, 49.1, 131.7, 56.6)
_ALLOWANCE_ROW = 13.0
_ALLOWANCE_INSET = 4.9

#: The 12pt bold the original shouts its payment clauses in.
_LOUD = Ink(bold=True, size=12)

_LEGAL_BLANKS = (
    ("Also Known as Legal Description; Lot #", "legal_lot"),
    ("Tract #", "legal_tract"),
    ("Block #", "legal_block"),
)


def build(sheet: Sheet) -> None:
    _details(sheet)
    sheet.restart()
    _payment(sheet)
    sheet.restart()
    _signatures(sheet)
    _terms(sheet)
    _footing(sheet)


def _footing(sheet: Sheet) -> None:
    """The initials strip repeated at the foot of every page.

    This is the one part of the form that is furniture rather than content, so
    it is a Word page footer: it stays at the foot however much is typed above
    it, and the number is a field so it stays right when pages are added. The
    modern layout has no such strip.
    """
    if not sheet.theme.banners:
        return
    sheet.standing(lambda *args: _foot(sheet, *args), bottom=FOOT_BOTTOM,
                   body_ends=TERMS_FOOT, first=True)


def _foot(sheet: Sheet, footer, section: int, alone: bool) -> None:
    """One footer: a ruled blank over each caption.

    Ruled with cell borders rather than the tab leaders Word would normally
    use for a fill-in blank, because a leader is only drawn on the way to
    something and the last of these has nothing after it.
    """
    theme = sheet.theme
    caption = Ink(size=theme.small)
    widths = _foot_columns(sheet.measure, theme.margin_x)
    blanks = range(1, len(widths) - 1, 2)

    footer.paragraphs[0]._p.getparent().remove(footer.paragraphs[0]._p)
    table = footer.add_table(rows=2, cols=len(widths), width=Pt(sheet.measure))
    fixed_widths(table, widths)
    cell_margins(table, left=0, right=0, top=0, bottom=0)
    table_indent(table, 0)
    borders(table, "all", weight=0, style="none")

    # The rules are the first row's underside, so the row itself is only as
    # tall as the border it carries.
    row_height(table, 0, FOOT_RULE, exact=True)
    for column in blanks:
        cell = table.cell(0, column)
        spacing(cell.paragraphs[0], line=FOOT_RULE)
        borders(cell, "bottom", weight=RULE, color=theme.line)

    row_height(table, 1, FOOT_CAPTION)
    for column, text in zip(blanks, FOOT_CAPTIONS):
        write(sheet.cell_line(table.cell(1, column), first=True,
                              size=theme.small, before=FOOT_DROP,
                              left=FOOT_CAPTION_INSET), text, caption)

    # Page one carries no number, and its strip sits higher. A footer is
    # measured from its foot, so the room comes off the bottom.
    if alone:
        spacing(footer.add_paragraph(), line=FOOT_FIRST_RISE)
        return

    line = sheet.cell_line(table.cell(1, 0), first=True, size=theme.small,
                           before=FOOT_PAGE_DROP, left=COLUMN)
    tab_stops(line, (LETTER / 2 - theme.margin_x, "center"))
    write(line, f"{FOOT_TITLE if section else ''}\tPage ", caption)
    page_number(line, caption)


def _foot_columns(measure: float, margin: float) -> list[float]:
    """The strip's cells: each blank, and the space on either side of it."""
    edges = [0.0]
    for start, end in FOOT_BLANKS:
        edges += [start - margin, end - margin]
    edges.append(measure)
    return [b - a for a, b in zip(edges, edges[1:])]


# ------------------------------------------------------------------- page 1


def _details(sheet: Sheet) -> None:
    theme = sheet.theme
    placed = theme.banners
    _masthead(sheet)

    sheet.banner("THIS AGREEMENT IS BETWEEN", at=BETWEEN[0],
                 text_at=BETWEEN[1], end=BETWEEN[2])
    letterhead(sheet, at=LETTERHEAD if placed else None, logo_left=LOGO_LEFT)

    sheet.para("THIS AGREEMENT IS ENTERED INTO", ink=sheet.ink(),
               at=ENTERED if placed else None, before=3, lead=ENTERED_LEAD,
               left=COLUMN)
    entered = sheet.para(lead=ENTERED_LEAD, left=COLUMN)
    write(entered, "THIS DATE: ", sheet.ink())
    sheet.field(entered, "agreement_date", "Month Year")

    party_table(
        sheet,
        at=PARTY if placed else None,
        gutter=[
            Caption(14.4, "and", left=38.8, ink=Ink(size=theme.size,
                                                    font=theme.display)),
            Caption(26.4, "BUYER/", left=36.0,
                    ink=Ink(size=theme.small, bold=True)),
            Caption(36.7, "OWNER", left=36.0,
                    ink=Ink(size=theme.small, bold=True)),
        ],
        name_field="buyer_name",
        address_label="ADDRESS",
        prefix="buyer",
    )

    sheet.para(str(legal()["hereinafter"]), ink=sheet.ink(size=theme.small),
               at=HEREINAFTER if placed else None, before=2,
               left=HEREINAFTER_LEFT - theme.margin_x)

    sheet.banner("ROOFING PROJECT", at=PROJECT[0], text_at=PROJECT[1],
                 end=PROJECT[2])
    _project_address(sheet)
    _legal_description(sheet)
    _scope(sheet)
    _allowances(sheet)


def _masthead(sheet: Sheet) -> None:
    """The title on the left, the cancellation notice on the right.

    They sit side by side, so they are a borderless two-column table -- the
    title's own box is only 329.6pt wide and the notice fills the rest.
    """
    theme = sheet.theme
    placed = theme.banners
    table = sheet.table(
        [MASTHEAD_WIDTH, sheet.measure - MASTHEAD_WIDTH],
        [BETWEEN[0] - MASTHEAD],
        at=MASTHEAD if placed else None,
        grid=False,
    )
    left, right = table.rows[0].cells

    big = Ink(bold=True, size=18, track=theme.tracking or None)
    title = sheet.cell_line(left, first=True, align="center", size=18,
                            lead=MASTHEAD_LEAD)
    sheet.field(title, "doc_title_line1", "Document title", ink=big)
    sheet.field(
        sheet.cell_line(left, align="center", size=18, lead=MASTHEAD_LEAD),
        "doc_title_line2", "", ink=big,
    )

    note = sheet.cell_line(left, align="center", size=theme.small,
                           before=COMPLIANCE - MASTHEAD - 2 * MASTHEAD_LEAD)
    sheet.field(note, "compliance", "", ink=sheet.ink(size=theme.small))

    intro = sheet.cell_line(right, first=True, align="justify",
                            before=INTRO - MASTHEAD, lead=INTRO_LEAD,
                            left=INTRO_LEFT - theme.margin_x - MASTHEAD_WIDTH,
                            right=sheet.measure - MASTHEAD_WIDTH
                            - (INTRO_LEFT - theme.margin_x - MASTHEAD_WIDTH)
                            - INTRO_WIDTH)
    write(intro, str(legal()["intro"]), sheet.ink())


def _project_address(sheet: Sheet) -> None:
    """The four-part project address, captioned above its values."""
    theme = sheet.theme
    columns = (
        ("PROJECT ADDRESS - STREET", "project_address", "Street"),
        ("CITY", "project_city", "City"),
        ("STATE", "project_state", "State"),
        ("ZIP CODE", "project_zip", "ZIP"),
    )
    widths = [b - a for a, b in zip(PROJECT_EDGES, PROJECT_EDGES[1:])]
    top = PROJECT[2] + 1
    table = sheet.table(widths, [LEGAL_RULE - top],
                        at=top if theme.banners else None, grid=False)

    for index, (caption, name, hint) in enumerate(columns):
        cell = table.cell(0, index)
        sheet.label(sheet.cell_line(cell, first=True, size=theme.small,
                                    before=PROJECT_LABEL - top,
                                    left=COLUMN), caption)
        # Only the street is set in from its column; the rest sit on it.
        sheet.field(sheet.cell_line(cell, left=PROJECT_STREET_INSET if index == 0
                                    else COLUMN), name, hint)


def _legal_description(sheet: Sheet) -> None:
    """Two lines of blanks identifying the parcel."""
    theme = sheet.theme
    placed = theme.banners
    blank = sheet.ink()
    sheet.rule(at=LEGAL_RULE if placed else None, before=1)

    first = sheet.para(at=LEGAL_TOP if placed else None, before=2,
                       left=COLUMN, lead=LEGAL_LEAD)
    for label, name in _LEGAL_BLANKS:
        write(first, f"{label} ", blank)
        sheet.field(first, name, "\u2014")
        write(first, "   ", blank)

    second = sheet.para(left=COLUMN, lead=LEGAL_LEAD)
    write(second, "Recorded in Book # ", blank)
    sheet.field(second, "legal_book", "\u2014")
    write(second, "   Page # ", blank)
    sheet.field(second, "legal_page", "\u2014")
    write(second, "   in the office of the County Recorder of ", blank)
    sheet.field(second, "legal_recorder", "County")
    write(second, " ", blank)
    sheet.field(second, "legal_state", "")

    sheet.rule(at=BODY_RULE if placed else None, before=1)


def _scope(sheet: Sheet) -> None:
    """The description of the work, then the warranty and the two checkboxes."""
    theme = sheet.theme
    margin = theme.margin_x
    placed = theme.banners

    rows = sheet.data.lists.get("scope", [])
    for index, row in enumerate(rows):
        style = row.get("style", "bullet")
        paragraph = sheet.bullet(
            at=BODY if placed and index == 0 else None,
            before=0 if index == 0 else BULLET_GAP,
            text=BULLET_TEXT - margin,
            marker=None if style == "plain" else BULLET_MARK - margin,
            lead=BULLET_LEAD,
        )
        sheet.cell_value(paragraph, "scope", index, "text",
                         "Describe the work\u2026",
                         ink=sheet.ink(bold=style == "bullet-bold"))

    warranty = sheet.para(before=WARRANTY[0], lead=WARRANTY[1], left=COLUMN)
    tab_stops(warranty, (WARRANTY_VALUE - margin, "left"))
    sheet.field(warranty, "warranty_prefix", "",
                ink=sheet.ink(color=theme.accent))
    write(warranty, "\t", sheet.ink())
    sheet.field(warranty, "warranty", "e.g. 5 yrs workmanship warranty")

    _check(sheet, "space_insufficient", legal()["spaceInsufficient"],
           before=CHECKS[0], lead=CHECKS[1])
    _check(sheet, "plans_attached", legal()["plansAttached"],
           before=CHECKS_SECOND[0], lead=CHECKS_SECOND[1])
    write(sheet.para(left=CHECK_TEXT - margin, lead=CHECKS_SECOND[1]),
          str(legal()["plansIncorporated"]),
          sheet.ink(bold=True, size=theme.small))

    sheet.rule(before=SCOPE_RULE)

    excluded = sheet.para(before=NOT_INCLUDED[0], lead=NOT_INCLUDED[1],
                          left=COLUMN, align="justify")
    write(excluded, "NOT INCLUDED: ", sheet.ink(bold=True))
    write(excluded, str(legal()["notIncluded"]) + " ", sheet.ink())
    sheet.field(excluded, "not_included", "items the owner provides")


def _check(sheet: Sheet, name: str, text, *, before: float, lead: float):
    """A checkbox with its clause hanging off it."""
    theme = sheet.theme
    margin = theme.margin_x
    paragraph = sheet.para(before=before, lead=lead,
                           left=CHECK_TEXT - margin,
                           hanging=CHECK_TEXT - CHECK_BOX)
    tab_stops(paragraph, (CHECK_TEXT - margin, "left"))
    sheet.check(paragraph, name)
    write(paragraph, "\t", sheet.ink())
    write(paragraph, str(text), sheet.ink(bold=True, size=theme.small))
    return paragraph


def _allowances(sheet: Sheet) -> None:
    intro = sheet.para(before=ALLOWANCES[0], lead=ALLOWANCES[1],
                       left=COLUMN, align="justify")
    write(intro, "ALLOWANCES: ", sheet.ink(bold=True))
    write(intro, str(legal()["allowances"]), sheet.ink())

    rows = sheet.data.lists.get("allowances", [])
    if rows:
        table = sheet.table(list(_ALLOWANCE_WIDTHS),
                            [_ALLOWANCE_ROW] * len(rows), before=2)

        for index in range(len(rows)):
            for slot, (description, amount) in enumerate(_ALLOWANCE_PAIRS):
                text = sheet.cell_line(table.cell(index, slot * 2), first=True,
                                       left=_ALLOWANCE_INSET)
                sheet.cell_value(text, "allowances", index, description, "Item")

                money = sheet.cell_line(table.cell(index, slot * 2 + 1),
                                        first=True, left=_ALLOWANCE_INSET)
                write(money, "$", sheet.ink())
                sheet.cell_value(money, "allowances", index, amount, "0.00")

    notes = sheet.para(before=NOTES, left=COLUMN)
    write(notes, "ADDITIONAL ALLOWANCES NOTES: ", sheet.ink())
    sheet.field(notes, "allowance_notes", "notes")


# ------------------------------------------------------------------- page 2


def _payment(sheet: Sheet) -> None:
    theme = sheet.theme
    placed = theme.banners
    body = sheet.ink()
    sheet.rule(at=PAY_RULE if placed else None)

    timing = sheet.para(at=PAY_TIMING if placed else None, align="left",
                        left=COLUMN, lead=PROSE_LEAD, lines=3)
    write(timing, "TIME FOR STARTING AND COMPLETION: ", sheet.ink(bold=True))
    write(timing, "The work to be performed by Contractor pursuant to this Agreement "
                  "shall be commenced within ", body)
    sheet.field(timing, "start_days", "days")
    write(timing, " (", body)
    sheet.field(timing, "start_days_num", "#")
    write(timing, ") days from this date or approximately on (Date): ", body)
    sheet.field(timing, "start_date", "date")
    write(timing, " and shall be substantially completed within ", body)
    sheet.field(timing, "complete_days", "days")
    write(timing, " (", body)
    sheet.field(timing, "complete_days_num", "#")
    write(timing, ") days or approximately on (Date): ", body)
    sheet.field(timing, "complete_date", "date")

    sheet.banner("CONTRACT PRICE", at=PRICE[0], text_at=PRICE[1], end=PRICE[2],
                 before=6)

    price = sheet.para(at=PAY_BODY if placed else None, align="left",
                       left=COLUMN, lead=PROSE_LEAD)
    write(price, "PAYMENT: ", sheet.ink(bold=True))
    write(price, "Owner agrees to pay Contractor a total price of ", body)
    sheet.field(price, "price_words", "amount in words")
    write(price, " Dollars (", body)
    sheet.field(price, "price_amount", "$0.00")
    write(price, ").", body)

    down = _prose(sheet, 22.3, loud=True, align="left")
    write(down, "Down Payment: ", _LOUD)
    sheet.field(down, "down_payment", "$0.00", ink=_LOUD)

    write(_prose(sheet, 0, loud=True, align="left", lines=2),
          str(legal()["downPaymentCap"]), _LOUD)

    sheet.field(_prose(sheet, 9.2, loud=True, align="left", lines=6),
                "progress_schedule",
                "Describe each payment and what it covers", ink=_LOUD)

    for gap, lines, text, loud, align in (
        (19.5, 3, legal()["scheduleMustDescribe"], True, "justify"),
        (3.4, 3, legal()["lienRelease"], False, "justify"),
        (11.5, 3, legal()["paymentTiming"], False, "justify"),
        (11.6, 3, " ".join(legal()["againstTheLaw"]), True, "left"),
        (4.9, 7, legal()["changeOrders"], False, "justify"),
        (11.5, 4, legal()["escrow"], False, "justify"),
        # The original breaks this clause across the page; keeping the halves
        # as they were printed is what puts the page break back where it was.
        (11.5, 3, legal()["doNotSign"][0], False, "justify"),
    ):
        write(_prose(sheet, gap, loud=loud, align=align, lines=lines),
              str(text), _LOUD if loud else body)


def _prose(sheet: Sheet, gap: float, *, loud: bool = False,
           align: str = "justify", at: float | None = None, lines: int = 1):
    """One of the standing clauses, at the original's own size and spacing."""
    size = 12.0 if loud else sheet.theme.size
    return sheet.para(at=at, before=gap, align=align, left=COLUMN, size=size,
                      lead=LOUD_LEAD if loud else PROSE_LEAD, lines=lines)


# ------------------------------------------------------------------- page 3


def _signatures(sheet: Sheet) -> None:
    theme = sheet.theme
    placed = theme.banners
    body = sheet.ink()

    write(_prose(sheet, 0, at=SIGN_TOP if placed else None, lines=2),
          str(legal()["doNotSign"][1]), body)

    sheet.banner("TERMS AND CONDITIONS", at=SIGN_BANNER[0],
                 text_at=SIGN_BANNER[1], end=SIGN_BANNER[2])

    write(_prose(sheet, 0, at=SIGN_BODY if placed else None, lines=4),
          str(legal()["entireAgreement"]), body)
    write(_prose(sheet, 13.5, align="center"), "NOTICE", sheet.ink(bold=True))
    write(_prose(sheet, 0, lines=5), str(legal()["licenseBoard"]),
          sheet.ink(bold=True))
    for gap, lines, text in (
        (11.5, 1, legal()["performanceBond"]),
        (11.5, 3, legal()["incorporatedDocuments"]),
    ):
        write(_prose(sheet, gap, lines=lines), str(text), body)

    write(_prose(sheet, 11.6, loud=True, align="left", lines=2),
          str(legal()["entitledToCopy"]), _LOUD)
    _cancel(sheet)
    _signature_grid(sheet)


def _cancel(sheet: Sheet) -> None:
    """The right-to-cancel clause, with its box against the right margin.

    A borderless two-column row rather than a tab stop, because the clause
    runs to three lines and the box belongs beside all of them.
    """
    theme = sheet.theme
    text = " ".join(legal()["rightToCancel"])
    if not theme.banners:
        # With no ruled boxes to hang it off, the clause simply follows its
        # own checkbox.
        return _check(sheet, "right_to_cancel", text, before=11.5,
                      lead=LOUD_LEAD)

    box = sheet.measure - (CANCEL_BOX - theme.margin_x)
    table = sheet.table([sheet.measure - box, box], [3 * LOUD_LEAD],
                        before=11.5, grid=False)

    write(sheet.cell_line(table.cell(0, 0), first=True, size=12,
                          lead=LOUD_LEAD, left=COLUMN), text, _LOUD)
    sheet.check(sheet.cell_line(table.cell(0, 1), first=True,
                                lead=CANCEL_SIZE, rule="atLeast"),
                "right_to_cancel", size=CANCEL_SIZE)


#: The signature block: where it starts, how wide its right-hand column is,
#: and for each of its two rows the drop to the signature line and the gap
#: between that line's rule and the caption under it.
SIGN_GRID = 392.4
#: The two signature slots split the measure, 18pt apart.
SIGN_GRID_LEFT = 315.0
SIGN_GUTTER = 18.0
SIGN_SLOT_INSET = 5.4
SIGN_CONSISTS_LEFT = 34.6
SIGN_DATE = 564.2
SIGN_DROPS = (9.5, 10.1)
SIGN_CAPTION_GAP = 6.0
SIGN_HEIGHTS = (36.5, 37.2)


def _signature_grid(sheet: Sheet) -> None:
    """The page count, then two owner slots with the contractor's beside them.

    A two-column borderless table: the owner signs twice on the right and the
    contractor once on the left, each over a ruled line with its caption
    under it.
    """
    theme = sheet.theme
    placed = theme.banners
    slot = (sheet.measure - SIGN_GUTTER) / 2

    consists = sheet.para(at=SIGN_GRID if placed else None, before=11.5,
                          left=SIGN_CONSISTS_LEFT, size=12, lead=LOUD_LEAD)
    write(consists, "THIS AGREEMENT CONSISTS OF ", _LOUD)
    sheet.field(consists, "consists_of_pages", "\u2014", ink=_LOUD)
    write(consists, " PAGES AND ", _LOUD)
    sheet.field(consists, "consists_of_attachments", "\u2014", ink=_LOUD)
    write(consists, " ATTACHMENTS", _LOUD)

    table = sheet.table([slot, SIGN_GUTTER, slot], list(SIGN_HEIGHTS),
                        grid=False)

    _slot(sheet, table.cell(0, 2), "owner_1", "OWNER/BUYER SIGNATURE",
          drop=SIGN_DROPS[0], date="owner_sig_date_1")
    _slot(sheet, table.cell(1, 0), "contractor", "CONTRACTOR SIGNATURE",
          drop=SIGN_DROPS[1])
    _slot(sheet, table.cell(1, 2), "owner_2", "OWNER/BUYER SIGNATURE",
          drop=SIGN_DROPS[1], date="owner_sig_date_2")


def _slot(sheet: Sheet, cell, name: str, caption: str, *, drop: float,
          date: str | None = None) -> None:
    """One signature: the line itself, ruled, with its caption beneath."""
    theme = sheet.theme
    cell.vertical_alignment = TOP

    line = sheet.cell_line(cell, first=True, before=drop, rule="atLeast",
                           left=SIGN_SLOT_INSET)
    if not sheet.signature(line, name, width=230):
        write(line, "X", sheet.ink(bold=True))
    if date:
        # The date sits against the right edge of the slot, as on the form.
        tab_stops(line, (SIGN_DATE - SIGN_GRID_LEFT, "left"))
        write(line, "\t", sheet.ink())
        sheet.field(line, date, "date")
    borders(line, "bottom", color=theme.line)

    write(sheet.cell_line(cell, size=theme.tiny, left=SIGN_SLOT_INSET,
                          before=SIGN_CAPTION_GAP),
          caption, Ink(size=theme.tiny))


# ----------------------------------------------------------------- pages 4-7


def _terms(sheet: Sheet) -> None:
    """The title page, then the terms themselves in two columns.

    The original typesets these as a pair of 263pt columns of 9pt text on
    10.3pt lines. Here they are a real two-column Word section, so the
    wording reflows between the columns when it is edited instead of each
    line being pinned where the original printed it.
    """
    theme = sheet.theme
    placed = theme.banners
    sheet.restart(at=TERMS_TITLE if placed else None)

    title = sheet.para(at=TERMS_TITLE if placed else None, align="center",
                       size=18)
    write(title, "TERMS AND CONDITIONS",
          Ink(bold=True, size=18, track=theme.tracking or None))

    section = two_column_section(sheet.document, space=TERMS_GUTTER)
    copy_page_setup(sheet.document.sections[0], section)
    if placed:
        section.top_margin = Pt(TERMS_TOP)
        section.left_margin = Pt(TERMS_EDGES[0])
        section.right_margin = Pt(612 - TERMS_EDGES[1])
        section.bottom_margin = Pt(792 - TERMS_FOOT)

    for block in terms():
        if block.heading:
            paragraph = keep_with_next(
                sheet.para(before=TERMS_HEADING, lead=TERMS_LEAD,
                           size=theme.small)
            )
            write(paragraph, block.text, Ink(bold=True, size=theme.small))
        else:
            paragraph = sheet.para(before=TERMS_GAP, lead=TERMS_LEAD,
                                   size=theme.small, align="justify")
            write(paragraph, block.text, Ink(size=theme.small))
