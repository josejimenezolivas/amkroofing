"""The shared surface the two Word templates are written against.

`Sheet` holds the document being assembled, the theme it is set in and the
data being poured into it, and exposes the handful of moves both templates
make: a rule, a banner, a bullet, an editable field.

The point of the Word export is that the file can be edited further in Word,
so everything here is built from constructs Word understands natively -- real
tables, real lists, real paragraphs. Nothing is positioned absolutely: typing
a longer address grows its row, the way it would in a document someone wrote
by hand.
"""

from __future__ import annotations

import base64
import binascii
from io import BytesIO
from itertools import count

from docx import Document as new_document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from .. import config
from ..models import DocumentData
from .kit import (
    ALIGN,
    Ink,
    RULE,
    Theme,
    _attr,
    _child,
    borders,
    cell_margins,
    fixed_widths,
    indent,
    page_frame,
    row_height,
    run_element,
    spacing,
    tab_stops,
    table_indent,
    write,
)

#: Width of the text column, in points, for whichever theme is in use.
#: US Letter, the paper every one of these forms is set on.
LETTER = 612.0
LENGTH = 792.0

CHECKED, UNCHECKED = "\u2612", "\u2610"
BULLET = "\u2022"


def _decode(data_url: str) -> bytes | None:
    """Pull the bytes out of a `data:image/...;base64,...` URL."""
    _, _, payload = data_url.partition(",")
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return None


class Sheet:
    """A Word document under construction.

    Blocks can be placed by measurement rather than by stacking. `at=` is the
    distance from the top of the page to the block's first line, taken
    straight off the reference PDF; the cursor tracks where the flow has
    reached and turns the difference into ordinary paragraph spacing. So the
    file reads like the original's coordinates while the document itself is
    still a plain Word document that reflows when edited.

    This only works because the classic theme pins its line boxes: with an
    exact leading every block's height is known in advance.
    """

    def __init__(self, data: DocumentData, theme: Theme) -> None:
        self.data = data
        self.theme = theme
        self.document = new_document()
        self._ids = count(880_000)

        #: How far down the page the flow has reached, in points.
        self.cursor = theme.margin_y
        self._previous: object | None = None
        #: Where new paragraphs go: the body, or the footer once it is open.
        self._host = self.document
        self._spare: object | None = None
        self._pending_break = False

        normal = self.document.styles["Normal"]
        normal.font.name = theme.body
        normal.font.size = Pt(theme.size)
        paragraph = normal.paragraph_format
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(0)
        paragraph.line_spacing = (
            Pt(theme.lead(theme.size)) if theme.exact_leading else theme.leading
        )

        section = self.document.sections[0]
        section.top_margin = Pt(theme.margin_y)
        section.bottom_margin = Pt(theme.margin_y)
        section.left_margin = Pt(theme.margin_x)
        section.right_margin = Pt(theme.margin_x)
        if theme.frame is not None:
            page_frame(section, theme.frame)

    @property
    def measure(self) -> float:
        """Width of the text column in points."""
        return LETTER - 2 * self.theme.margin_x

    # --------------------------------------------------------------- placing

    def _paragraph(self):
        if self._spare is not None:
            paragraph, self._spare = self._spare, None
        else:
            paragraph = self._host.add_paragraph()
        if self._pending_break:
            paragraph.paragraph_format.page_break_before = True
            self._pending_break = False
        return paragraph

    def _gap(self, at: float | None, before: float) -> float:
        """Space needed above the next block to honour a measured position."""
        if at is None:
            return before
        return max(0.0, round(at - self.cursor, 2))

    def footer(self, bottom: float) -> None:
        """Move into the page footer, which ends `bottom` points down the page.

        The sign-off is pushed to the bottom of the sheet with `margin-top:
        auto`, which a flow cannot do. Word's answer is a page footer, so that
        is what this is: it holds its place however much is typed above it,
        and the body is stopped short of it. Everything written from here on
        goes into the footer, and because a footer grows upwards from its
        bottom edge the blocks inside it are spaced rather than placed.
        """
        section = self.document.sections[0]
        section.footer_distance = Pt(LENGTH - bottom)
        section.bottom_margin = Pt(LENGTH - bottom)
        self._host = section.footer
        self._host.is_linked_to_previous = False
        # A footer arrives with one paragraph of its own, which is the first
        # line rather than a spare.
        self._spare = self._host.paragraphs[0]
        self.cursor = bottom
        self._previous = None

    def standing(self, build, *, bottom: float, body_ends: float,
                 first: bool = False) -> None:
        """Repeat a strip at the foot of every page.

        Furniture rather than a block: `build` is handed each section's footer
        along with that section's number and whether this is the separate one
        only page one sees, and nothing it writes moves the cursor. `bottom`
        is where the strip's last line ends and `body_ends` where the text
        above it stops, both measured from the top of the page as everything
        else is.
        """
        for index, section in enumerate(self.document.sections):
            section.footer_distance = Pt(LENGTH - bottom)
            section.bottom_margin = Pt(LENGTH - body_ends)
            section.footer.is_linked_to_previous = False
            build(section.footer, index, False)
            if first and index == 0:
                section.different_first_page_header_footer = True
                build(section.first_page_footer, index, True)

    def restart(self, at: float | None = None) -> None:
        """Begin a new page; the cursor returns to the top margin.

        The break is carried until the next block and set on it, rather than
        written as a break of its own: a paragraph holding nothing but a page
        break still takes a line at the top of the new page.
        """
        self._pending_break = True
        self.cursor = at if at is not None else self.theme.margin_y
        self._previous = None

    # ------------------------------------------------------------ paragraphs

    def para(
        self,
        text: str = "",
        *,
        ink: Ink | None = None,
        align: str = "left",
        at: float | None = None,
        before: float = 0,
        after: float = 0,
        size: float | None = None,
        lead: float | None = None,
        lines: int = 1,
        rule: str = "exact",
        left: float = 0,
        right: float = 0,
        hanging: float = 0,
    ):
        """A paragraph, optionally placed at a measured coordinate.

        `lines` is how many lines the block fills in the original. It only
        matters when something below is placed by measurement: the space
        above a block is worked out from where the flow has reached, and the
        flow cannot be known without it. Set it wrong and the block below
        shifts; leave it at one and a wrapping paragraph pushes everything
        after it down.
        """
        size = self.theme.size if size is None else size
        lead = self.theme.lead(size) if lead is None else lead
        before = self._gap(at, before)

        paragraph = self._paragraph()
        paragraph.alignment = ALIGN[align]
        spacing(paragraph, before=before, after=after, line=lead, rule=rule)
        if left or hanging:
            indent(paragraph, left=left, hanging=hanging)
        if right:
            paragraph.paragraph_format.right_indent = Pt(right)
        if text:
            write(paragraph, text, ink or Ink(size=size))

        self.cursor += before + lines * lead + after
        self._previous = paragraph
        return paragraph

    def ink(self, *, size: float | None = None, **kwargs) -> Ink:
        """An `Ink` defaulting to the theme's body size."""
        return Ink(size=self.theme.size if size is None else size, **kwargs)

    def label(self, paragraph, text: str):
        """The caption that sits above a value in a ruled box."""
        return write(
            paragraph,
            text,
            Ink(
                size=self.theme.small,
                color=self.theme.dim,
                caps=self.theme.banners,
                track=self.theme.tracking or None,
                bold=not self.theme.banners,
            ),
        )

    def rule(
        self,
        *,
        at: float | None = None,
        before: float = 0,
        after: float = 0,
        weight: int = RULE,
        left: float = 0,
        right: float = 0,
    ):
        """A ruled line occupying `at` to `at` + the rule's own weight.

        Drawn as a paragraph's *top* border, so the line lands on the top of
        the line box and therefore exactly on the measured coordinate. The
        border sits above that box and takes its own width from the flow, so
        the cursor is advanced twice.
        """
        thickness = weight / 8
        paragraph = self.para(at=at, before=before, after=after,
                              lead=thickness, left=left, right=right)
        borders(paragraph, "top", weight=weight, color=self.theme.line)
        self.cursor += thickness
        return paragraph

    def banner(
        self,
        text: str,
        *,
        at: float | None = None,
        text_at: float | None = None,
        end: float | None = None,
        before: float = 0,
        after: float = 0,
        size: float | None = None,
    ):
        """A section heading ruled above and below, as the form prints them.

        The modern theme has no rules, so it states the heading once, quietly.
        """
        if not self.theme.banners:
            return self.para(
                text,
                ink=Ink(bold=True, size=self.theme.tiny, color=self.theme.dim,
                        caps=True, track=self.theme.tracking),
                before=before + 6,
                after=3,
            )

        self.rule(at=at, before=before)
        paragraph = self.para(text, at=text_at, align="center",
                              ink=self.ink(bold=True, size=size))
        self.rule(at=end, after=after)
        return paragraph

    def bullet(
        self,
        *,
        at: float | None = None,
        before: float = 0,
        after: float = 0,
        text: float,
        marker: float | None,
        lead: float | None = None,
        right: float = 0,
    ):
        """A hanging-indent bullet, `text` points in from the text margin.

        Written as an indented paragraph with a literal bullet rather than a
        numbering definition: the scope list is a free-form set of lines that
        someone will add to and reorder in Word, and a real list would keep
        renumbering itself around them.
        """
        paragraph = self.para(
            at=at,
            before=before,
            after=after,
            lead=lead,
            left=text,
            right=right,
            hanging=0 if marker is None else text - marker,
        )
        if marker is not None:
            tab_stops(paragraph, (text, "left"))
            write(paragraph, f"{BULLET}\t", self.ink())
        return paragraph

    # ---------------------------------------------------------------- fields

    def field(self, paragraph, name: str, placeholder: str = "", *,
              ink: Ink | None = None):
        """Write a value, or a Word placeholder when the document is blank."""
        return self._editable(paragraph, self.data.fields.get(name, ""), name,
                              placeholder, ink)

    def cell_value(self, paragraph, list_name: str, index: int, key: str,
                   placeholder: str = "", *, ink: Ink | None = None):
        rows = self.data.lists.get(list_name, [])
        value = rows[index].get(key, "") if index < len(rows) else ""
        return self._editable(paragraph, value, f"{list_name}.{index}.{key}",
                              placeholder, ink)

    def _editable(self, paragraph, value: str, tag: str, placeholder: str,
                  ink: Ink | None):
        value = (value or "").strip()
        if value:
            return write(paragraph, value, ink)
        if not placeholder:
            return None
        return self._placeholder(paragraph, tag, placeholder, ink)

    def _placeholder(self, paragraph, tag: str, text: str, ink: Ink | None):
        """A plain-text content control showing its prompt.

        This is the mechanism Word's own templates use. The prompt is greyed
        out and the control selects as a single object, so clicking it once
        and typing replaces it with normally-formatted text. Writing a grey
        run instead would leave the typing grey.
        """
        sdt = OxmlElement("w:sdt")
        properties = OxmlElement("w:sdtPr")
        sdt.append(properties)

        # Word wants these in schema order: alias, tag, id, placeholder, then
        # the marker saying the prompt is showing, then the control's type.
        alias = OxmlElement("w:alias")
        _attr(alias, "val", text)
        properties.append(alias)

        marker = OxmlElement("w:tag")
        _attr(marker, "val", tag)
        properties.append(marker)

        identifier = OxmlElement("w:id")
        _attr(identifier, "val", next(self._ids))
        properties.append(identifier)

        properties.append(OxmlElement("w:showingPlcHdr"))
        properties.append(OxmlElement("w:text"))

        content = OxmlElement("w:sdtContent")
        content.append(
            run_element(
                text,
                Ink(
                    size=ink.size if ink else None,
                    font=ink.font if ink else None,
                    italic=True,
                    color="808080",
                ),
            )
        )
        sdt.append(content)
        paragraph._p.append(sdt)
        return sdt

    def check(self, paragraph, name: str, *, size: float | None = None):
        on = bool(self.data.checks.get(name))
        return write(
            paragraph,
            CHECKED if on else UNCHECKED,
            Ink(font="Segoe UI Symbol",
                size=self.theme.size + 1.5 if size is None else size),
        )

    # ---------------------------------------------------------------- images

    def picture(self, paragraph, image: bytes, width: float,
                height: float | None = None) -> None:
        """Place an image, optionally fitted inside a width x height box.

        Fitting matters for the logo: the original occupies a particular
        footprint, and a replacement of any proportion has to sit inside it
        rather than push everything below it down the page. This is what the
        page's `object-fit: contain` does.
        """
        run = paragraph.add_run()
        if height is None:
            run.add_picture(BytesIO(image), width=Pt(width))
            return

        shape = run.add_picture(BytesIO(image))
        scale = min(width / shape.width.pt, height / shape.height.pt)
        shape.width = Pt(shape.width.pt * scale)
        shape.height = Pt(shape.height.pt * scale)

    def signature(self, paragraph, name: str, width: float) -> bool:
        """Place a captured signature; returns whether there was one."""
        raw = self.data.signatures.get(name)
        image = _decode(raw) if raw else None
        if not image:
            return False
        self.picture(paragraph, image, width)
        return True

    def logo(self, paragraph, width: float, height: float | None = None) -> None:
        raw = self.data.images.get("logo")
        image = _decode(raw) if raw else None
        if image is None and config.LOGO.exists():
            image = config.LOGO.read_bytes()
        if image:
            self.picture(paragraph, image, width, height)

    # ---------------------------------------------------------------- tables

    def table(
        self,
        widths: list[float],
        heights: list[float],
        *,
        at: float | None = None,
        before: float = 0,
        left: float = 0,
        grid: bool = True,
        weight: int = RULE,
        pad: float = 0.0,
    ):
        """A table of known column widths and row heights, both in points.

        Heights are "at least", so a row holds its measured height until
        someone types enough to need another line, at which point it grows
        rather than swallowing the text. They are measured rule to rule: a
        ruled row stands as tall as its content plus the border below it, so
        the border comes back off the height asked for here.
        """
        gap = self._gap(at, before)
        if self._previous is not None:
            # Tables have no space above them, so the room comes from the
            # paragraph before.
            spacing(self._previous, after=gap)
        elif self._touching_table():
            # Word runs two tables together into one if nothing separates
            # them, and the second one's borders and indent win -- so a
            # paragraph always goes between, as short as it is allowed to be.
            spacing(self._paragraph(), line=max(gap, 0.05))
        elif gap:
            spacing(self._paragraph(), line=gap)

        table = self.document.add_table(rows=len(heights), cols=len(widths))
        fixed_widths(table, widths)
        cell_margins(table, left=pad, right=pad, top=0, bottom=0)
        table_indent(table, left)

        thickness = weight / 8 if grid else 0.0
        for index, height in enumerate(heights):
            row_height(table, index, max(0.0, height - thickness))

        if grid:
            borders(table, "all", weight=weight, color=self.theme.line)
            for edge in ("insideH", "insideV"):
                element = _child(_child(table._tbl.tblPr, "tblBorders"), edge)
                _attr(element, "val", "single")
                _attr(element, "sz", weight)
                _attr(element, "color", self.theme.line)
        else:
            borders(table, "all", style="nil")
            for edge in ("insideH", "insideV"):
                element = _child(_child(table._tbl.tblPr, "tblBorders"), edge)
                _attr(element, "val", "nil")

        self.cursor += gap + sum(heights) + thickness
        # A table cannot carry trailing space, so the next block asks for its
        # own gap from scratch.
        self._previous = None
        return table

    def _touching_table(self) -> bool:
        """Whether the last block written was a table.

        The body's final child is the section's own properties, so the last
        block is the one before whatever trails it.
        """
        # The document keeps its blocks one level down, in the body; a footer
        # is its own container.
        container = getattr(self._host, "_body", self._host)
        blocks = [
            element
            for element in container._element.iterchildren()
            if element.tag in (qn("w:p"), qn("w:tbl"))
        ]
        return bool(blocks) and blocks[-1].tag == qn("w:tbl")

    def cell_line(
        self,
        cell,
        *,
        first: bool = False,
        before: float = 0,
        size: float | None = None,
        lead: float | None = None,
        rule: str = "exact",
        align: str = "left",
        left: float = 0,
        right: float = 0,
    ):
        """A line inside a table cell, `before` points below what precedes it.

        Cells have no padding, so a caption or value is positioned by its own
        space above -- which is how the reference's offsets from a row's top
        rule can be transcribed directly.
        """
        size = self.theme.size if size is None else size
        paragraph = cell.paragraphs[0] if first else cell.add_paragraph()
        paragraph.alignment = ALIGN[align]
        spacing(paragraph, before=before, after=0, rule=rule,
                line=self.theme.lead(size) if lead is None else lead)
        if left:
            indent(paragraph, left=left)
        if right:
            paragraph.paragraph_format.right_indent = Pt(right)
        return paragraph

    def first(self, cell):
        """A cell's opening paragraph."""
        return self.cell_line(cell, first=True)

    def line(self, cell):
        """Another paragraph in the same cell."""
        return self.cell_line(cell)

    def centre(self, paragraph):
        paragraph.alignment = ALIGN["center"]
        return paragraph

    def emptied(self, cell):
        """Drop the spare paragraphs a merge leaves behind.

        Merging concatenates the cells' contents, so a merge of three empty
        cells yields three empty paragraphs and a cell three lines tall.
        """
        for paragraph in cell.paragraphs[1:]:
            paragraph._p.getparent().remove(paragraph._p)
        return cell

    def stacked(self, cell, caption: str, *, before: float = 0,
                left: float = 0):
        """A ruled-box cell: small caption over the value beneath it."""
        self.label(
            self.cell_line(cell, first=True, before=before, left=left,
                           size=self.theme.tiny),
            caption,
        )
        return self.cell_line(cell, left=left)
