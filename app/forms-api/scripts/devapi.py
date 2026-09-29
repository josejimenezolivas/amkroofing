"""Shared helpers for the dev check scripts.

These scripts work by making a real document and driving the real UI, which
means they litter the document list unless they tidy up. `scratch()` removes
whatever a check created, including when the check fails partway through.

The API wants a signed-in user, so each run signs in as a local dev-checks
user by writing a session straight into the local database, and removes that
session when it exits.
"""

import atexit
import sys
import urllib.parse
from contextlib import contextmanager
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import accounts, db  # noqa: E402

API = "http://127.0.0.1:8000/forms"
APP = "http://localhost:5173/forms/"
DEV_EMAIL = "dev-checks@amkroofing.test"


def _sign_in() -> str:
    if urllib.parse.urlsplit(db.url()).hostname not in ("127.0.0.1", "localhost"):
        raise SystemExit("The dev checks only sign in to a local database; unset DATABASE_URL.")
    if accounts.get_user(DEV_EMAIL) is None:
        accounts.invite(DEV_EMAIL)
    session_id = accounts.start_session(DEV_EMAIL)
    atexit.register(accounts.end_session, session_id)
    return session_id


SESSION_ID = _sign_in()

#: A requests session carrying the dev-checks sign-in.
http = requests.Session()
http.cookies.set(accounts.SESSION_COOKIE, SESSION_ID, path="/forms")


async def signed_in_page(browser, **options):
    """A fresh page, already signed in, for driving the UI at APP."""
    context = await browser.new_context(**options)
    await context.add_cookies(
        [{"name": accounts.SESSION_COOKIE, "value": SESSION_ID, "domain": "localhost", "path": "/forms"}]
    )
    return await context.new_page()


def documents() -> list[dict]:
    return http.get(f"{API}/api/documents", timeout=30).json()


#: The transcriptions of the PDFs in `references/`, seeded at server startup.
REFERENCE_IDS = {"invoice": "reference-invoice", "agreement": "reference-agreement"}


def create(template: str, style: str = "classic", data: dict | None = None) -> dict:
    return http.post(
        f"{API}/api/documents",
        json={"template": template, "style": style, "data": data},
        timeout=30,
    ).json()


def copy_of_reference(template: str, style: str = "classic") -> dict:
    """A throwaway document holding the reference content.

    Checks run against a copy so they can restyle and edit freely without
    disturbing the seeded reference documents in the user's list.
    """
    source = http.get(f"{API}/api/documents/{REFERENCE_IDS[template]}", timeout=30).json()
    return create(template, style, source["data"])


@contextmanager
def scratch():
    """Delete every document that appears while the block runs."""
    before = {doc["id"] for doc in documents()}
    try:
        yield
    finally:
        for doc in documents():
            if doc["id"] not in before:
                http.delete(f"{API}/api/documents/{doc['id']}", timeout=30)
