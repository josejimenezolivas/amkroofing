"""Word building blocks.

python-docx covers paragraphs, runs and tables but stops short of most
formatting, so the pieces that need raw WordprocessingML -- borders, shading,
fixed column widths, multi-column sections -- are wrapped here once.

Everything is measured in points, the same unit the classic layouts use, so a
measurement taken off the reference PDF can be typed straight in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import (WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT,
                            WD_TAB_LEADER)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .order import ORDER

#: Eighths of a point, the unit Word measures border weights in.
HAIRLINE = 4
RULE = 8

Edges = str  # any of "top", "bottom", "left", "right", or "all"


def _attr(element, name: str, value) -> None:
    element.set(qn(f"w:{name}"), str(value))


def _child(parent, tag: str):
    """Fetch `parent`'s `w:tag`, creating it in schema order if it is missing.

    Word will not open a document whose property elements are out of order --
    `w:pBdr` before `w:spacing` inside `w:pPr`, and so on -- and appending is
    only right by luck. `ORDER` is generated from the schema itself.
    """
    found = parent.find(qn(f"w:{tag}"))
    if found is not None:
        return found

    found = OxmlElement(f"w:{tag}")
    sequence = ORDER.get(f"w:{etree.QName(parent).localname}", ())
    if tag in sequence:
        later = set(sequence[sequence.index(tag) + 1:])
        for sibling in parent:
            if etree.QName(sibling).localname in later:
                sibling.addprevious(found)
                return found
    parent.append(found)
    return found


def _properties(target):
    """The `w:pPr` / `w:tcPr` / `w:tblPr` element for whatever was passed."""
    if isinstance(target, Paragraph):
        return target.paragraph_format.element.get_or_add_pPr()
    if isinstance(target, _Cell):
        return target._tc.get_or_add_tcPr()
    if isinstance(target, Table):
        return target._tbl.tblPr
    raise TypeError(f"no properties for {type(target).__name__}")


def _border_tag(target) -> str:
    return {Paragraph: "pBdr", _Cell: "tcBorders", Table: "tblBorders"}[type(target)]


def borders(
    target,
    edges: Edges = "all",
    *,
    weight: int = HAIRLINE,
    color: str = "000000",
    style: str = "single",
) -> None:
    """Draw or erase borders on a paragraph, cell or table.

    Pass `edges` as a space-separated list ("top bottom") or "all", and
    `style="nil"` to remove one. Cells inherit the table's borders, so hiding
    an inner rule means setting it to nil on the cell, not omitting it.
    """
    names = ["top", "left", "bottom", "right"] if edges == "all" else edges.split()
    holder = _child(_properties(target), _border_tag(target))

    for name in names:
        edge = _child(holder, name)
        _attr(edge, "val", style)
        _attr(edge, "sz", weight)
        _attr(edge, "space", 0)
        _attr(edge, "color", color)


def shade(target, fill: str) -> None:
    element = _child(_properties(target), "shd")
    _attr(element, "val", "clear")
    _attr(element, "color", "auto")
    _attr(element, "fill", fill)


def spacing(
    paragraph: Paragraph,
    *,
    before: float | None = None,
    after: float | None = None,
    line: float | None = None,
    rule: str = "exact",
) -> Paragraph:
    """Set paragraph spacing in points.

    `rule` is Word's line rule: "exact" pins the line box to `line`, which is
    what the classic forms need because the original sets a tighter leading
    than Times New Roman's natural one. "atLeast" lets a line grow, and
    "auto" treats `line` as a multiple.

    Word has no negative paragraph spacing, so a gap that has already been
    used up by taller text above simply becomes nothing.
    """
    fmt = paragraph.paragraph_format
    if before is not None:
        fmt.space_before = Pt(max(0.0, before))
    if after is not None:
        fmt.space_after = Pt(max(0.0, after))
    if line is not None:
        element = _child(_properties(paragraph), "spacing")
        _attr(element, "line", int(round(line * 20)))
        _attr(element, "lineRule", rule)
    return paragraph


def indent(paragraph: Paragraph, left: float = 0, hanging: float = 0) -> Paragraph:
    fmt = paragraph.paragraph_format
    fmt.left_indent = Pt(left)
    if hanging:
        fmt.first_line_indent = Pt(-hanging)
    return paragraph


def keep_with_next(paragraph: Paragraph) -> Paragraph:
    paragraph.paragraph_format.keep_with_next = True
    return paragraph


_TABS = {
    "left": WD_TAB_ALIGNMENT.LEFT,
    "center": WD_TAB_ALIGNMENT.CENTER,
    "right": WD_TAB_ALIGNMENT.RIGHT,
}


#: A tab can rule the space it crosses. "underscore" is how Word draws a
#: fill-in blank, so the blank stays a blank rather than becoming a graphic.
_LEADERS = {None: WD_TAB_LEADER.SPACES, "underscore": WD_TAB_LEADER.LINES}


def tab_stops(paragraph: Paragraph, *stops) -> Paragraph:
    """Add tab stops as (position in points, one of left/center/right).

    A third element names the rule the tab draws on its way to the stop.
    """
    for position, alignment, *leader in stops:
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Pt(position), _TABS[alignment], _LEADERS[leader[0] if leader else None]
        )
    return paragraph


def page_number(paragraph: Paragraph, ink: Ink | None = None) -> Paragraph:
    """The page's own number, as a field rather than a typed-in figure.

    Word recomputes it, so the numbering survives whatever is added above.
    """
    run = write(paragraph, "", ink)
    for tag, attribute in (("fldChar", "begin"), ("instrText", None),
                           ("fldChar", "end")):
        element = OxmlElement(f"w:{tag}")
        if attribute is None:
            element.set(qn("xml:space"), "preserve")
            element.text = " PAGE "
        else:
            _attr(element, "fldCharType", attribute)
        run._r.append(element)
    return paragraph


def cell_margins(target, *, left: float = 0, right: float = 0, top: float = 0,
                 bottom: float = 0) -> None:
    """Padding inside a cell, or the default for every cell of a table.

    The edges are named "left" and "right" rather than the schema's "start"
    and "end": both are legal, but only these are honoured by the readers that
    matter, and a cell whose margin is ignored falls back to Word's 0.08in
    default -- which is 5.76pt of drift.
    """
    tag = "tblCellMar" if isinstance(target, Table) else "tcMar"
    holder = _child(_properties(target), tag)
    for name, value in (("top", top), ("left", left), ("bottom", bottom),
                        ("right", right)):
        element = _child(holder, name)
        _attr(element, "w", int(value * 20))  # twentieths of a point
        _attr(element, "type", "dxa")


def fixed_widths(table: Table, widths: list[float]) -> None:
    """Pin column widths in points.

    Word only honours these if the table is told not to autofit, and the width
    has to be repeated on every cell -- the grid alone is advisory.
    """
    table.autofit = False
    layout = _child(table._tbl.tblPr, "tblLayout")
    _attr(layout, "type", "fixed")

    total = _child(table._tbl.tblPr, "tblW")
    _attr(total, "w", int(sum(widths) * 20))
    _attr(total, "type", "dxa")

    # The grid is what a reader lays out against before it reaches the cells,
    # so leaving it at python-docx's even split makes the table flash wrong.
    for column, width in zip(table._tbl.tblGrid, widths):
        _attr(column, "w", int(width * 20))

    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Pt(width)


def row_height(table: Table, index: int, height: float, exact: bool = False) -> None:
    element = _child(_child(table.rows[index]._tr, "trPr"), "trHeight")
    _attr(element, "val", int(round(height * 20)))
    _attr(element, "hRule", "exact" if exact else "atLeast")


def table_indent(table: Table, points: float) -> None:
    """Shift a table sideways from the text margin. Negative is allowed."""
    element = _child(table._tbl.tblPr, "tblInd")
    _attr(element, "w", int(round(points * 20)))
    _attr(element, "type", "dxa")


def page_frame(section, inset: float, weight: int = RULE, color: str = "000000") -> None:
    """The ruled box drawn inside every page edge.

    Word calls this a page border and measures the inset from the paper edge
    rather than from the text margin, which is how the original is drawn.
    """
    borders_element = _child(section._sectPr, "pgBorders")
    _attr(borders_element, "offsetFrom", "page")
    for edge in ("top", "left", "bottom", "right"):
        element = _child(borders_element, edge)
        _attr(element, "val", "single")
        _attr(element, "sz", weight)
        _attr(element, "space", int(round(inset)))
        _attr(element, "color", color)


def two_column_section(document, *, space: float = 18.0, continuous: bool = False):
    """Start a section that flows in two columns, as the terms pages do."""
    section = document.add_section(
        WD_SECTION.CONTINUOUS if continuous else WD_SECTION.NEW_PAGE
    )
    columns = _child(section._sectPr, "cols")
    _attr(columns, "num", 2)
    _attr(columns, "space", int(space * 20))
    _attr(columns, "equalWidth", 1)
    return section


def copy_page_setup(source, target) -> None:
    for name in (
        "page_width", "page_height", "orientation",
        "left_margin", "right_margin", "top_margin", "bottom_margin",
    ):
        setattr(target, name, getattr(source, name))


# --------------------------------------------------------------------- theme


@dataclass(frozen=True)
class Theme:
    """Typography for one of the two designs.

    The classic theme reproduces the reference form, which sets everything in
    Times at 8, 9, 10, 12 and 18pt and reaches for Arial once, in the invoice's
    sign-off. The modern theme drops the rules and sets everything in one
    humanist sans, matching the on-screen redesign.
    """

    body: str
    #: The sans face the design uses for display flourishes.
    display: str
    #: Body text.
    size: float
    #: Captions and the ruled boxes' labels.
    small: float
    #: The smallest text on the form.
    tiny: float
    #: Rules, box edges and the hairlines inside tables.
    line: str
    #: Secondary text: labels, captions, hints.
    dim: str
    accent: str
    #: Page margins, in points.
    margin_y: float
    margin_x: float
    #: Line spacing as a multiple of the font size.
    leading: float
    #: Whether that leading is pinned exactly.
    #:
    #: The classic form sets 1.107 -- the height of Times New Roman's glyph
    #: box, and tighter than the font's natural line -- so it only comes out
    #: right if the line box is exact. That is also what makes the layout
    #: predictable enough to place blocks at measured coordinates. The modern
    #: layout has no such constraint and leaves lines free to grow.
    exact_leading: bool
    #: The ruled box inside the page edge, as an inset from the paper edge.
    frame: float | None = None
    #: Uppercase section banners, as the printed form has them.
    banners: bool = True
    tracking: float = 0.0
    fills: dict[str, str] = field(default_factory=dict)

    def lead(self, size: float) -> float:
        """Line height in points for text at `size`."""
        return size * self.leading


#: Every measurement here is off the reference PDFs: 10pt Times New Roman on
#: 11.07pt lines, Arial for the ruled-box captions, a text column running
#: 30.6pt to 581.4pt, and the 1pt frame 24pt inside the paper edge.
CLASSIC = Theme(
    body="Times New Roman",
    display="Arial",
    size=10.0,
    small=9.0,
    tiny=8.0,
    line="000000",
    dim="000000",
    accent="000099",
    margin_y=30.6,
    margin_x=30.6,
    leading=1.107,
    exact_leading=True,
    frame=24.0,
    banners=True,
)

#: The modern layout is set in the browser in SF Pro, which exists on no
#: Windows machine and is not licensed to embed. Calibri ships with Office on
#: both platforms, so the recipient sees what was intended rather than
#: whatever Word decided to substitute.
MODERN = Theme(
    body="Calibri",
    display="Calibri",
    size=9.5,
    small=8.0,
    tiny=7.0,
    line="D2D2D7",
    dim="6E6E73",
    accent="0071E3",
    margin_y=54.0,
    margin_x=61.2,
    leading=1.45,
    exact_leading=False,
    banners=False,
    tracking=0.6,
    fills={"surface": "F5F5F7"},
)

THEMES = {"classic": CLASSIC, "modern": MODERN}


# ------------------------------------------------------------------- writing


@dataclass
class Ink:
    """How a run of text is set."""

    bold: bool = False
    italic: bool = False
    size: float | None = None
    font: str | None = None
    color: str | None = None
    caps: bool = False
    #: Letter-spacing in points, for the modern theme's tracked-out labels.
    track: float | None = None
    underline: bool = False


def run_element(text: str, ink: Ink | None = None):
    """Build a `w:r` from scratch.

    Runs are also needed in places python-docx offers no cursor for, such as
    inside a content control, so they are assembled here rather than through
    `Paragraph.add_run`.
    """
    ink = ink or Ink()
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    run.append(properties)

    if ink.font:
        fonts = _child(properties, "rFonts")
        # The complex-script and East-Asian slots have to name the font too,
        # or Word falls back for anything outside Latin-1.
        for slot in ("ascii", "hAnsi", "cs", "eastAsia"):
            _attr(fonts, slot, ink.font)
    if ink.bold:
        _child(properties, "b")
    if ink.italic:
        _child(properties, "i")
    if ink.caps:
        _child(properties, "caps")
    if ink.underline:
        _attr(_child(properties, "u"), "val", "single")
    if ink.track:
        _attr(_child(properties, "spacing"), "val", int(ink.track * 20))
    if ink.size is not None:
        for tag in ("sz", "szCs"):
            _attr(_child(properties, tag), "val", int(ink.size * 2))  # half-points
    if ink.color:
        _attr(_child(properties, "color"), "val", ink.color)

    # A run may hold several text nodes with breaks and tabs between them,
    # which is how a value typed across several lines keeps them. Both are
    # elements of their own: a literal tab inside a `w:t` is just whitespace,
    # so it neither advances to a tab stop nor draws the stop's leader.
    for index, line in enumerate(text.split("\n")):
        if index:
            run.append(OxmlElement("w:br"))
        for position, piece in enumerate(line.split("\t")):
            if position:
                run.append(OxmlElement("w:tab"))
            if not piece:
                continue
            body = OxmlElement("w:t")
            body.set(qn("xml:space"), "preserve")
            body.text = piece
            run.append(body)
    return run


def write(paragraph: Paragraph, text: str, ink: Ink | None = None) -> Run:
    """Append a run to a paragraph."""
    element = run_element(text, ink)
    paragraph._p.append(element)
    return Run(element, paragraph)


ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

MIDDLE = WD_ALIGN_VERTICAL.CENTER
TOP = WD_ALIGN_VERTICAL.TOP
