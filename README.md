# AMK Roofing

[amkroofing.com](https://amkroofing.com)

The marketing site is static HTML. Invoice and agreement forms live at
[amkroofing.com/forms](https://amkroofing.com/forms). Vercel serves both from this repo:
the page and `/forms` are static, and `/forms/api` is the forms server. The
roof-scan routes stay at `/api/solar`, `/api/geocode`, and `/api/tiles`.

The Vercel project Root Directory is `app`.

## Run the marketing site

The roof scan fetches JSON from `assets/scans/`, which browsers block on
`file://` URLs. Serve the folder over HTTP.

```bash
cd app
python3 -m http.server 4321
```

Open [http://127.0.0.1:4321](http://127.0.0.1:4321).

That serves the static page only. `/api/solar`, `/api/geocode`, and `/api/tiles`
are Vercel Functions, so under `python3 -m http.server` they 404 and the map
falls back to free Esri imagery with no Solar data. Use `vercel dev` from
`app/` to exercise that flow.

This command does not serve the forms app. The forms UI is produced by a build.

## Run the site with forms

You need **Python 3.11+** and **Node 18+**.

```bash
# terminal 1 — API
cd app/forms-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
env -u PLAYWRIGHT_BROWSERS_PATH .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# terminal 2 — site, including /forms
cd app
node scripts/build.js
python3 scripts/serve.py
```

Open [http://127.0.0.1:4321/forms](http://127.0.0.1:4321/forms).
`curl http://127.0.0.1:8000/forms/api/health` should return `{"status":"ok"}`.
API docs are at <http://127.0.0.1:8000/docs>.

`--reload` is optional. `env -u PLAYWRIGHT_BROWSERS_PATH` matters when that
variable is set in the shell: Playwright then looks in a cache that does not
hold the Chromium installed by `playwright install`. Install and run with the
variable unset so the browser stays in the default cache.

For UI work with hot reload, leave the API running and use the Vite server:

```bash
cd app/forms-web
npm install
npm run dev
```

Open [http://localhost:5173/forms/](http://localhost:5173/forms/). Vite proxies
`/forms/api` to port 8000.

## Using the forms

Each form has two layouts over the same data. **Classic** reproduces the
printed original. **Modern** is the same clauses and fields, set more cleanly.
The Classic/Modern tab in the toolbar switches between them.

**Start a form.** Click *Invoice* or *Agreement* under "New document". That
opens a draft. Nothing is stored until you press **Save**, so browsing the
templates does not fill the document list. Once saved, edits autosave.

**Fill it in.** Click any text to edit it. Empty fields show a grey
placeholder. Placeholders are screen-only and never appear in an export, so a
half-finished form still prints clean. Rows in the scope, summary, and
allowance lists have `+`/`−` controls that appear on hover.

**Sign it.** Click a signature line to draw with the mouse or a trackpad.

**Change the logo.** Click the logo in the letterhead and pick an image. It is
stored with that document and travels into both exports. Art of any proportion
is fitted into the original's footprint.

**Export.** The *Export* button offers PDF or Microsoft Word.

The list always contains *Reference — Roofing Job Invoice* and *Reference —
Residential Roofing Agreement*: the two PDFs in `app/references/`, transcribed.
They are ordinary documents you can read, edit, or copy from. They are created
at startup only if missing, so edits survive a restart and a deleted one comes
back.

Saved documents are JSON files in `app/forms-api/data/documents` when you run
the API yourself. On Vercel the container disk is wiped when an instance scales
to zero, so production needs a Blob store connected to the project
(`BLOB_READ_WRITE_TOKEN`). The forms API has no login: anyone who can open
`/forms` can read and edit saved documents.

## How exporting works

**PDF is a photograph of the page.** The browser sends the document's markup
plus every stylesheet to the server, and headless Chromium prints it. An
export matches the screen because it is the screen. Editing affordances live
in `@media screen`, so they are absent in print.

**Word is a document you can keep working on.** `app/forms-api/app/word/`
composes a real `.docx` from the document's data using Word's own tables,
lists, paragraphs, and content controls. Nothing is positioned absolutely, so
typing a longer address in Word grows its row and the rest of the form moves
with it.

The Word file is a second implementation of the layout. It shares the source
data, the legal wording in `app/forms-web/src/forms/legal.json`, and the terms
in `app/forms-api/app/terms.json`. Handing Word the page's HTML produces a web
page with a document extension, and the absolute positioning that makes the
classic forms pixel-exact is what makes them unusable to edit after import.

Blank fields export as Word content controls with a grey prompt, the same
mechanism Word's own templates use. Click one and type, and the text comes out
normally formatted.

Worth knowing:

- The Word file is not pixel-identical to the PDF. Treat the PDF as the
  accurate copy and Word as the editable one.
- `app/forms-api/scripts/check_docx.py` validates every export against the
  ECMA-376 WordprocessingML schema in `app/forms-api/schemas/`. Word is strict
  about the order of property elements and reports "unreadable content" when
  it is wrong, so `app/forms-api/app/word/order.py` is generated from that
  schema.
- Line spacing is a multiple, never a fixed measure. Exact leading crops
  anything taller than it, so a pasted image or a bumped font size in a
  document someone keeps editing would lose its top and bottom.
- The modern layout is set in Calibri in the Word file. The screen uses SF Pro,
  which is not on Windows and cannot be embedded.

`legal.json` and the logo belong to the React app. The container only sees
`app/forms-api/`, so copies live in `app/forms-api/vendor`.
`node scripts/build.js` refreshes those copies and stops if they changed.
Commit `forms-api/vendor` in the same change.

## Layout

```
app/                         Vercel project root
  index.html                 marketing site
  api/                       /api/solar, /api/geocode, /api/tiles
  assets/                    logo, video, cached roof scans
  references/                the two source PDFs the forms were transcribed from
  forms-web/                 Vite + React + TypeScript, served at /forms
    src/App.tsx              sidebar, toolbar, draft/save flow
    src/components/          Editable, fields, LogoField, SignatureField
    src/forms/               classic layouts, pixel-matched to the originals
      legal.json             the contract's fixed wording; the server reads it too
      termsLines.ts          generated: the terms, line by line, at exact positions
      modern/                modern layouts
    src/lib/                 API client, document store, export
  forms-api/                 FastAPI, routed at /forms/api
    app/main.py              app setup, CORS, startup seeding
    app/models.py            Pydantic models for documents and render requests
    app/templates.py         blank templates: letterhead and standing text only
    app/reference.py         the two reference PDFs, transcribed
    app/storage.py           JSON files locally, Vercel Blob when the token is set
    app/pdf.py               HTML -> PDF via headless Chromium
    app/terms.json           generated: the agreement's terms, line by line
    app/word/                data -> .docx
    vendor/                  copies of legal.json and the logo for the container
    schemas/                 ECMA-376 schemas, for validating the Word export
    scripts/                 dev checks
  scripts/build.js           marketing site + /forms into dist/
  scripts/serve.py           dist/ on :4321, proxying /forms/api to :8000
```

The classic layout is written in points, so the markup shares the PDF's
612×792pt coordinate space and positions can be copied straight out of the
original. The default `line-height: 1.107` is the height of Times New Roman's
glyph box, which makes an element's CSS top edge coincide with the text
bounding box a PDF viewer reports.

The agreement's terms pages are generated. The reference embeds only subsets
of its fonts, so they cannot be reused, and macOS Times New Roman is about 4%
wider — enough to change every line break. `scripts/generate_terms.py`
extracts each line's exact position from the PDF into `termsLines.ts`, and the
classic pages place them verbatim. The modern layout reflows those same lines
back into paragraphs, using "this line was justified" to mean "the paragraph
continues".

## Dev checks

These drive the real UI in a browser. They need both servers running, and they
clean up after themselves.

```bash
cd app/forms-api

# Render both forms and diff them against references/ as overlay images.
.venv/bin/python scripts/compare_to_reference.py

# Assert the editing affordances move nothing: exits non-zero if an empty
# form lays out differently from a filled one.
.venv/bin/python scripts/check_blank_layout.py

# Export both formats through the Export menu and report what came out.
.venv/bin/python scripts/check_export.py

# Validate the Word export: valid package, schema-valid XML, expected content.
.venv/bin/python scripts/check_docx.py

# Render the Word exports to PNGs. Needs LibreOffice: brew install --cask libreoffice
.venv/bin/python scripts/preview_docx.py

# Render the modern layouts to PNGs for review.
.venv/bin/python scripts/preview_modern.py

# Regenerate the terms from the reference PDF (writes the TS and the JSON).
.venv/bin/python scripts/generate_terms.py

# Regenerate app/word/order.py from schemas/wml.xsd.
.venv/bin/python scripts/generate_docx_order.py
```

`check_docx.py`, `generate_docx_order.py`, and `preview_docx.py` do not need a
running server. `preview_docx.py` is worth the LibreOffice install:
`check_docx.py` can prove the file is a valid package containing the right
content, and LibreOffice is an independent reader, so rendering through it
shows whether the file looks like a roofing invoice and whether it opens at
all. The server never touches LibreOffice.

Output lands in `app/forms-api/.compare/`. `compare_to_reference.py` prints a
mean ink difference per page: the reference is tinted red and the render blue
and the two are multiplied, so shared ink goes black and anything misplaced
stays coloured.

## The Google API key

`GOOGLE_MAPS_API_KEY` is a **server-side secret**. It is never written into the page.

Everything that touches Google goes through the proxy in `app/api/`, which reads the key
from the environment and enforces a service-area bounding box, a per-IP rate limit, and an
origin check before forwarding. `scripts/config.js` is generated at build time and holds
nothing but the satellite-engine flag.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GOOGLE_MAPS_API_KEY` | yes, for the roof scan | — | Server-side key for Solar, Geocoding, and Map Tiles. Without it `/api/solar`, `/api/geocode`, and `/api/tiles` return 503. |
| `TILE_PROVIDER` | no | `google` | `google` for Map Tiles via `/api/tiles`; `osm` for free Esri imagery and zero Google tile spend. |
| `SERVICE_AREA_BBOX` | no | `36.5,-123.6,38.9,-120.9` | `minLat,minLon,maxLat,maxLon`. Requests outside are rejected before they cost anything. |
| `ALLOWED_ORIGINS` | no | `amkroofing.com,www.amkroofing.com` | Comma-separated hosts allowed to call `/api/*`. |
| `RATE_MAX_HITS` / `RATE_WINDOW_MS` | no | `40` / `60000` | Per-IP request budget for the roof-scan proxy. |
| `BLOB_READ_WRITE_TOKEN` | yes, for saved forms in production | — | Private blob store for documents. Set by connecting a Vercel Blob store. |

The rate limit is in-memory, so it is per-instance and resets on cold start. It raises the
cost of casual scripting; it is not a distributed limiter. **The hard ceiling on the bill is
the per-API daily quota cap in Google Cloud Console** — set those as well.
