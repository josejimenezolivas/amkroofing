"""Bring the database up to date: the schema, then the reference documents.

Both steps are idempotent. Deploys run this once as the forms service's build
command (`python -m app.migrate`); locally the API runs it on startup.
"""

from . import db, storage


def run() -> None:
    db.migrate()
    storage.seed_reference_documents()


if __name__ == "__main__":
    run()
    db.close()
    print("Database is up to date.")
