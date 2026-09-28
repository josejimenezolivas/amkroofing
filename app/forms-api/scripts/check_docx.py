"""Check that the Word export is a valid, complete .docx.

Three passes, strongest last:

1. the package -- it is a zip, the content types are declared, and every
   relationship points at a part that is actually in the archive;
2. the grammar -- `word/document.xml` validates against the ECMA-376
   WordprocessingML schema in `server/schemas`;
3. the content -- python-docx reopens the file and finds the tables, images
   and text the document is supposed to contain.

Exits non-zero on any failure, so it works as a gate.
"""

import posixpath
import sys
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import word  # noqa: E402
from app.models import WordRequest  # noqa: E402
from app.reference import REFERENCE_AGREEMENT, REFERENCE_INVOICE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas" / "wml.xsd"
OUT = ROOT / ".compare"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
RELS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"

CASES = [
    ("invoice", REFERENCE_INVOICE),
    ("agreement", REFERENCE_AGREEMENT),
]

#: Text every export must carry, proving the data actually made it across.
EXPECTED = {
    "invoice": ["ROOFING JOB INVOICE", "AMK ROOFING", "Jeff Westererine",
                "SUMMARY", "$8,094.00", "Thank You!"],
    "agreement": ["RESIDENTIAL ROOFING", "Michaeal", "3360 Ramona st",
                  "ALLOWANCES", "TERMS AND CONDITIONS", "ASBESTOS",
                  "THE DOWN PAYMENT MAY NOT EXCEED"],
}

failures: list[str] = []


def fail(label: str, message: str) -> None:
    failures.append(f"{label}: {message}")
    print(f"    FAIL  {message}")


def check_package(label: str, path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken:
            fail(label, f"corrupt entry {broken}")
            return

        names = set(archive.namelist())
        for required in ("[Content_Types].xml", "_rels/.rels",
                         "word/document.xml", "word/styles.xml"):
            if required not in names:
                fail(label, f"missing {required}")

        # Every relationship must resolve, or Word reports unreadable content.
        for entry in names:
            if not entry.endswith(".rels"):
                continue
            base = entry.rsplit("_rels/", 1)[0]
            tree = etree.fromstring(archive.read(entry))
            for relationship in tree.findall(f"{RELS}Relationship"):
                if relationship.get("TargetMode") == "External":
                    continue
                target = relationship.get("Target")
                resolved = posixpath.normpath(
                    target[1:] if target.startswith("/") else base + target
                )
                if resolved not in names:
                    fail(label, f"{entry} points at missing {resolved}")

        print(f"    package ok ({len(names)} parts)")


def check_schema(label: str, path: Path, schema: etree.XMLSchema) -> None:
    with zipfile.ZipFile(path) as archive:
        document = etree.fromstring(archive.read("word/document.xml"))

    # Markup Compatibility attributes are a separate specification layered on
    # top of ECMA-376; wml.xsd knows nothing about them, so they come off
    # before validating the document that remains.
    for name in list(document.attrib):
        if name.startswith(f"{{{MC}}}"):
            del document.attrib[name]

    if schema.validate(document):
        print("    schema ok (ECMA-376 WordprocessingML)")
        return
    for problem in schema.error_log[:5]:
        fail(label, f"line {problem.line}: {problem.message}")


def check_content(label: str, path: Path, expected: list[str]) -> None:
    document = Document(path)

    text = "\n".join(p.text for p in document.paragraphs)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                text += "\n" + cell.text
    # Anything pinned to the foot of the sheet -- the invoice's sign-off, the
    # agreement's initials strip -- lives in a footer rather than the body.
    for section in document.sections:
        for footer in (section.footer, section.first_page_footer):
            text += "\n" + "\n".join(p.text for p in footer.paragraphs)

    missing = [phrase for phrase in expected if phrase not in text]
    if missing:
        fail(label, f"text not found: {', '.join(missing)}")

    with zipfile.ZipFile(path) as archive:
        images = [name for name in archive.namelist()
                  if name.startswith("word/media/")]
    if not images:
        fail(label, "no images embedded (the logo should be)")

    controls = len(document.element.body.findall(f".//{W}sdt"))
    print(f"    {len(document.tables)} tables, {len(document.paragraphs)} paragraphs, "
          f"{len(images)} images, {controls} placeholders")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    schema = etree.XMLSchema(etree.parse(SCHEMAS))

    for template, data in CASES:
        for style in ("classic", "modern"):
            label = f"{template}/{style}"
            print(f"{label}")

            path = OUT / f"w-{template}-{style}.docx"
            path.write_bytes(
                word.render_docx(
                    WordRequest(template=template, style=style, data=data,
                                filename=template)
                )
            )

            check_package(label, path)
            check_schema(label, path, schema)
            check_content(label, path, EXPECTED[template])

    print()
    if failures:
        print(f"{len(failures)} problem(s)")
        return 1
    print("all exports are valid Open XML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
