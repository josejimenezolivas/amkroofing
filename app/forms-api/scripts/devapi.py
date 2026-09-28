"""Shared helpers for the dev check scripts.

These scripts work by making a real document and driving the real UI, which
means they litter the document list unless they tidy up. `scratch()` removes
whatever a check created, including when the check fails partway through.
"""

from contextlib import contextmanager

import requests

API = "http://127.0.0.1:8000/forms"
APP = "http://localhost:5173/forms/"


def documents() -> list[dict]:
    return requests.get(f"{API}/api/documents", timeout=30).json()


#: The transcriptions of the PDFs in `references/`, seeded at server startup.
REFERENCE_IDS = {"invoice": "reference-invoice", "agreement": "reference-agreement"}


def create(template: str, style: str = "classic", data: dict | None = None) -> dict:
    return requests.post(
        f"{API}/api/documents",
        json={"template": template, "style": style, "data": data},
        timeout=30,
    ).json()


def copy_of_reference(template: str, style: str = "classic") -> dict:
    """A throwaway document holding the reference content.

    Checks run against a copy so they can restyle and edit freely without
    disturbing the seeded reference documents in the user's list.
    """
    source = requests.get(
        f"{API}/api/documents/{REFERENCE_IDS[template]}", timeout=30
    ).json()
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
                requests.delete(f"{API}/api/documents/{doc['id']}", timeout=30)
