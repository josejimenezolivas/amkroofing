"""Vercel Blob backend for saved forms.

The container filesystem is wiped when an instance scales to zero, so production
stores each document as a private blob. Local development keeps the JSON files
and only uses this module when BLOB_READ_WRITE_TOKEN is set.

The HTTP shape matches @vercel/blob: PUT /?pathname= with x-api-version 12.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://vercel.com/api/blob"
PREFIX = "amk-forms/documents/"


class BlobError(RuntimeError):
    pass


def enabled() -> bool:
    return bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))


def _token() -> str:
    token = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
    if not token:
        raise BlobError("BLOB_READ_WRITE_TOKEN is not set")
    return token


def _store_id(token: str) -> str | None:
    explicit = os.environ.get("BLOB_STORE_ID")
    if explicit:
        return explicit
    # vercel_blob_rw_<storeId>_<secret>
    parts = token.split("_")
    if len(parts) >= 5 and parts[0] == "vercel" and parts[1] == "blob":
        return parts[3]
    return None


def _headers(token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "authorization": f"Bearer {token}",
        "x-api-version": "12",
    }
    store = _store_id(token)
    if store:
        headers["x-vercel-blob-store-id"] = store
    if extra:
        headers.update(extra)
    return headers


def _call(method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> bytes:
    token = _token()
    request = urllib.request.Request(
        f"{API}{path}",
        data=body,
        method=method,
        headers=_headers(token, headers),
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise BlobError(f"Blob {method} {path} failed: {exc.code} {detail}") from exc


def pathname(document_id: str) -> str:
    if not document_id or "/" in document_id or "\\" in document_id or document_id.startswith("."):
        raise BlobError(f"Refusing document id {document_id!r}")
    return f"{PREFIX}{document_id}.json"


def put_text(document_id: str, text: str) -> None:
    name = pathname(document_id)
    query = urllib.parse.urlencode({"pathname": name})
    _call(
        "PUT",
        f"/?{query}",
        body=text.encode("utf-8"),
        headers={
            "x-content-type": "application/json",
            "x-add-random-suffix": "0",
            "x-allow-overwrite": "1",
            "x-vercel-blob-access": "private",
        },
    )


def delete_pathname(document_id: str) -> bool:
    blobs = _list_prefix(pathname(document_id))
    urls = [blob["url"] for blob in blobs if blob.get("url")]
    if not urls:
        return False
    payload = json.dumps({"urls": urls}).encode("utf-8")
    _call("POST", "/delete", body=payload, headers={"content-type": "application/json"})
    return True


def read_text(document_id: str) -> str | None:
    matches = _list_prefix(pathname(document_id))
    if not matches:
        return None
    return _download(matches[0])


def read_all() -> list[str]:
    return [_download(blob) for blob in _list_prefix(PREFIX)]


def _list_prefix(prefix: str) -> list[dict]:
    found: list[dict] = []
    cursor: str | None = None
    while True:
        params: dict[str, str] = {"prefix": prefix, "limit": "1000"}
        if cursor:
            params["cursor"] = cursor
        raw = _call("GET", f"/?{urllib.parse.urlencode(params)}")
        page = json.loads(raw.decode("utf-8"))
        found.extend(page.get("blobs") or [])
        if not page.get("hasMore") or not page.get("cursor"):
            return found
        cursor = page["cursor"]


def _download(blob: dict) -> str:
    url = blob.get("downloadUrl") or blob.get("url")
    if not url:
        raise BlobError(f"Blob {blob.get('pathname')} has no url")
    token = _token()
    request = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise BlobError(f"Blob download failed: {exc.code} {detail}") from exc
