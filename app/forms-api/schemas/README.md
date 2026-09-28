# ECMA-376 schemas

The WordprocessingML schemas, used by `scripts/check_docx.py` to validate the
Word export against the published grammar rather than against Word's tolerance
for malformed files.

These are the ECMA-376 Transitional schemas as redistributed by Apache POI
(`poi-ooxml-full`, Apache License 2.0). Only the files reachable from
`wml.xsd` are kept. To refresh them, pull a newer `poi-ooxml-full` jar and copy
across `org/apache/poi/schemas/ooxml/src/wml.xsd` plus everything its
`schemaLocation` imports pull in, transitively.

One edit is made to the copy: `wml.xsd` imports the `xml` namespace without a
`schemaLocation`, which leaves `xml:space` dangling and any strict parser
refusing to load the schema at all. `xml.xsd` from <https://www.w3.org/2001/xml.xsd>
is vendored alongside and the import points at it.

Word is stricter than most readers about the order of children inside
`w:pPr`, `w:rPr` and `w:sdtPr`, and a schema check catches exactly that class
of mistake — one that otherwise only shows up as "Word found unreadable
content" on the user's machine.
