#!/usr/bin/env python3
"""Serve the built site and proxy /forms/api to the forms server.

    # terminal 1
    cd app/forms-api
    uvicorn app.main:app --host 127.0.0.1 --port 8000

    # terminal 2
    cd app
    node scripts/build.js
    python3 scripts/serve.py
"""

from __future__ import annotations

import http.server
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "dist"
API = "http://127.0.0.1:8000"
PORT = 4321


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def do_PUT(self):
        self._route()

    def do_DELETE(self):
        self._route()

    def _route(self):
        path = self.path.split("?", 1)[0]
        if path == "/forms" or path.startswith("/forms/api"):
            if path.startswith("/forms/api"):
                self._proxy()
                return
        if path in ("/forms", "/forms/"):
            self.path = "/forms/index.html"
        super().do_GET() if self.command == "GET" else self.send_error(405)

    def _proxy(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        request = urllib.request.Request(API + self.path, data=body, method=self.command)
        content_type = self.headers.get("Content-Type")
        if content_type:
            request.add_header("Content-Type", content_type)
        origin = self.headers.get("Origin")
        if origin:
            request.add_header("Origin", origin)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
                self.send_response(response.status)
                self._forward(response.headers, payload)
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            self._forward(exc.headers, payload)
            self.wfile.write(payload)
        except urllib.error.URLError as exc:
            payload = f"Forms API is not running at {API} ({exc.reason})".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _forward(self, headers, payload: bytes) -> None:
        for key in ("Content-Type", "Content-Disposition"):
            value = headers.get(key)
            if value:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()


def main() -> None:
    if not (ROOT / "index.html").is_file():
        raise SystemExit(f"Missing {ROOT / 'index.html'}. Run: node scripts/build.js")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Serving {ROOT} at http://127.0.0.1:{PORT}  (forms API -> {API})")
    server.serve_forever()


if __name__ == "__main__":
    main()
