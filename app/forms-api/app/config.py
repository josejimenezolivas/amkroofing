import os
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent

# The React app is the source of truth for the logo and the legal wording.
# The deployed service cannot see that tree, so it uses the copies in vendor/.
# scripts/build.js refuses to build the site if those copies are stale.
WEB_SRC = SERVER_ROOT.parent / "forms-web" / "src"
VENDOR = SERVER_ROOT / "vendor"


def _shared(live: Path, name: str) -> Path:
    return live if live.is_file() else VENDOR / name


# The logo the Word export falls back to when a document has not replaced it.
LOGO = _shared(WEB_SRC / "assets" / "amk-logo.png", "amk-logo.png")

# The agreement's standing legal wording, shared with the browser so the two
# layouts and the two export formats cannot drift apart.
LEGAL_PROSE = _shared(WEB_SRC / "forms" / "legal.json", "legal.json")

# Pages 5-7 of the agreement, one entry per typeset line of the original.
TERMS_LINES = SERVER_ROOT / "app" / "terms.json"

# Origins that may call the API from another host. The production site is
# same-origin, so this list is for the Vite dev server and the local combined server.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "https://amkroofing.com",
    "https://www.amkroofing.com",
]

# The Chromium service in app/forms-pdf. On Vercel a service binding sets this;
# locally that service runs on port 8001.
PDF_SERVICE_URL = os.environ.get("PDF_SERVICE_URL") or "http://127.0.0.1:8001"

# US Letter in CSS points, matching the source PDFs' 612x792 media box.
PAGE_WIDTH = "612pt"
PAGE_HEIGHT = "792pt"
