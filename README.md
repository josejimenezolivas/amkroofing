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

You need **Python 3.11+**, **Node 18+**, and **Docker** for the local Postgres.

```bash
# once — Postgres from compose.yaml at the repo root, on :5432
docker compose up -d --wait db

# terminal 1 — API
cd app/forms-api
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
env -u PLAYWRIGHT_BROWSERS_PATH .venv/bin/playwright install chromium
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# terminal 2 — PDF renderer, headless Chromium; only PDF export uses it
cd app/forms-pdf
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
env -u PLAYWRIGHT_BROWSERS_PATH .venv/bin/playwright install chromium
env -u PLAYWRIGHT_BROWSERS_PATH .venv/bin/uvicorn renderer.main:app --host 127.0.0.1 --port 8001

# terminal 3 — site, including /forms
cd app
node scripts/build.js
python3 scripts/serve.py
```

Open [http://127.0.0.1:4321/forms](http://127.0.0.1:4321/forms).
`curl http://127.0.0.1:8000/forms/api/health` should return `{"status":"ok"}`.
API docs are at <http://127.0.0.1:8000/docs>.

The API forwards PDF exports to the renderer at `PDF_SERVICE_URL`, which
defaults to `http://127.0.0.1:8001`. Everything else works without it, and a
PDF export fails with a 502 until it is running. On Vercel the renderer is a
separate container with no public route, so a cold start of the API never
waits for a browser to launch.

`requirements-dev.txt` adds Playwright and PyMuPDF for the checks in
`scripts/`; the deployed API installs only `requirements.txt`. `--reload` is
optional. `env -u PLAYWRIGHT_BROWSERS_PATH` matters when that variable is set
in the shell: Playwright then looks in a cache that does not hold the Chromium
installed by `playwright install`. Install and run with the variable unset so
the browser stays in the default cache.

For UI work with hot reload, leave the API running and use the Vite server:

```bash
cd app/forms-web
npm install
npm run dev
```

Open [http://localhost:5173/forms/](http://localhost:5173/forms/). Vite proxies
`/forms/api` to port 8000 and serves the marketing page at `/`, so the logo's
home link stays local (its `/api/*` functions still 404, as under `http.server`).

The API creates its tables on startup. The forms ask you to sign in: invite
yourself into the local database and open the link it prints to choose a
password:

```bash
cd app/forms-api
.venv/bin/python scripts/users.py invite you@example.com
# for the :4321 server instead: ... invite you@example.com --site http://127.0.0.1:4321
```

"Continue with Google" appears only when `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` are set for the API; see [Sign-in](#sign-in).

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
along with the schema, only if missing, so edits survive a restart and a
deleted one comes back on the next deploy.

Documents, users, and sessions live in Postgres, in their own `forms` schema:
`forms.documents`, `forms.users`, `forms.sessions`. Locally that is the
`compose.yaml` database; in production it is Neon, via `DATABASE_URL`. The
schema is in `app/forms-api/app/db.py`. `python -m app.migrate` applies it and
runs as the forms service's build command on every deploy; locally the API
runs it on startup. Each statement is written to be safe to repeat.

## Sign-in

Every forms API route except `/forms/api/health` and `/forms/api/auth/*`
requires a signed-in user, and `/forms` shows a sign-in page until there is
one. The page itself is public; the documents behind it are not.

**Access is by invitation.** There is no public sign-up. Inviting an email
creates the user and prints a one-time link, good for 7 days:

```bash
cd app/forms-api
.venv/bin/python scripts/users.py invite someone@example.com --site https://www.amkroofing.com
.venv/bin/python scripts/users.py list
.venv/bin/python scripts/users.py remove someone@example.com   # also signs them out everywhere
```

The script edits whichever database `DATABASE_URL` names, the local one by
default. For production, copy `DATABASE_URL` from Vercel → Storage → your Neon
database → `.env.local` and prefix the command with it. The script prints which
host it is about to change.

The invited person then signs in one of two ways:

- **Email and password.** The invite link opens a "Set up your account" form
  with a live password checklist: at least 10 characters, 3 of 4 character
  kinds, not a common password, nothing from their name or email, no runs like
  `aaaa` or `1234`. `app/forms-api/app/password.py` enforces the same rules the
  page shows. Inviting someone again issues a new link, which is how a
  forgotten password is reset.
- **Google.** "Continue with Google" signs in any Google account whose
  verified email has been invited, with no link needed.

How it works, after Intentra's sign-in:

- Passwords are hashed with Argon2id. A wrong password and an unknown email
  get the same answer, and ten failures lock an address for 15 minutes (per
  instance).
- A session is an opaque random id in an `httpOnly`, `SameSite=Lax` cookie
  scoped to `/forms`, valid 30 days. The server stores only its SHA-256 in
  `forms.sessions`, and every request checks it with one indexed query.
  Signing out deletes the row, and removing a user cascades to all of theirs,
  so access ends on the next request.
- Accepting an invite sets the password and spends the link in a single
  `UPDATE ... WHERE invite_hash = ...`, so a link works once even if two
  requests race.
- Google uses the redirect flow: `/forms/api/auth/google/start` sends the
  browser to Google's account chooser with a CSRF `state` cookie, and
  `/forms/api/auth/google/callback` checks the state, trades the code for an
  ID token using the client secret, checks its audience, issuer, expiry and
  verified email, and looks the email up in the invite list.

**Production setup, once:**

1. Add a Neon Postgres database to the project (Storage → Create → Neon). This
   sets `DATABASE_URL`, the pooled connection string the API uses. The tables
   are created on the first request after the deploy.
2. In Google Cloud Console → APIs & Services → Credentials, create an OAuth
   client of type *Web application* with these authorized redirect URIs:
   - `https://www.amkroofing.com/forms/api/auth/google/callback`
   - `http://localhost:5173/forms/api/auth/google/callback` (Vite dev)
   - `http://127.0.0.1:4321/forms/api/auth/google/callback` (combined local server)
3. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to the Vercel project and
   redeploy.
4. Invite the first people with the production `DATABASE_URL`, as above.

The redirect URI is built from the browser's origin (`X-Forwarded-Host` and
`X-Forwarded-Proto`), so it must be registered for every origin you sign in
from. Visit `www.amkroofing.com` rather than `amkroofing.com`; the latter
redirects there anyway.

## How exporting works

**PDF is a photograph of the page.** The browser sends the document's markup
plus every stylesheet to the server, and headless Chromium in
`app/forms-pdf/` prints it. An
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

`legal.json` and the logo belong to the React app. The deployed API only sees
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
    src/Gate.tsx             sign-in page or the app, depending on the session
    src/Login.tsx            the sign-in page and the invite form
    src/App.tsx              sidebar, toolbar, draft/save flow
    src/components/          Editable, fields, LogoField, SignatureField
    src/forms/               classic layouts, pixel-matched to the originals
      legal.json             the contract's fixed wording; the server reads it too
      termsLines.ts          generated: the terms, line by line, at exact positions
      modern/                modern layouts
    src/lib/                 API client, document store, export, password checklist
  forms-api/                 FastAPI, routed at /forms/api
    app/main.py              app setup, CORS, the sign-in guard
    app/migrate.py           schema and reference documents; the deploy's build step
    app/accounts.py          users, invites, Argon2id passwords, sessions
    app/google.py            Google sign-in: redirect, code exchange, ID token checks
    app/password.py          the password rules
    app/routers/auth.py      /forms/api/auth/*
    app/db.py                Postgres: connection pool and the forms schema
    app/models.py            Pydantic models for documents and render requests
    app/templates.py         blank templates: letterhead and standing text only
    app/reference.py         the two reference PDFs, transcribed
    app/storage.py           documents in forms.documents
    app/routers/render.py    exports: Word here, PDF forwarded to forms-pdf
    app/terms.json           generated: the agreement's terms, line by line
    app/word/                data -> .docx
    vendor/                  copies of legal.json and the logo for the deployed API
    schemas/                 ECMA-376 schemas, for validating the Word export
    scripts/                 dev checks, and users.py for invites
  forms-pdf/                 private container: HTML -> PDF via headless Chromium
    renderer/main.py         POST /render, reachable only through the API's binding
    renderer/pdf.py          the browser, and the print settings
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
clean up after themselves. They sign in as a local `dev-checks@amkroofing.test`
user by writing a session into the database and delete it on exit, and they
refuse to run against anything but a local database.

```bash
cd app/forms-api

# Sign-in, the guard, and document saves, in process with Google stubbed. Needs
# the local Postgres but no API server: it creates a scratch database and drops
# it afterwards.
.venv/bin/python scripts/check_auth.py

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
| `DATABASE_URL` | yes, for the forms in production | local `compose.yaml` Postgres | Postgres for the forms' documents, users, and sessions. Set by adding a Neon database to the project. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | no | — | OAuth web client for "Continue with Google" on `/forms`. Without both, only email and password sign-in is offered. |

The rate limit is in-memory, so it is per-instance and resets on cold start. It raises the
cost of casual scripting; it is not a distributed limiter. **The hard ceiling on the bill is
the per-API daily quota cap in Google Cloud Console** — set those as well.
