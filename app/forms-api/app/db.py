"""Postgres: the forms' users, sessions, and documents.

Production uses the Neon database connected to the Vercel project, which sets
DATABASE_URL. Locally it defaults to the Postgres in the repo's compose.yaml:
`docker compose up -d --wait db` from the repo root.

The tables live in their own `forms` schema, so they can share a database with
the rewrite's Drizzle tables in `public` without colliding.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

LOCAL_URL = "postgresql://amk:amk@127.0.0.1:5432/amk"

# Applied on every startup, so each statement must be safe to repeat. A change
# to an existing table needs an `alter table ... if not exists` here too.
SCHEMA = """
create schema if not exists forms;

create table if not exists forms.users (
    email text primary key check (email = lower(email)),
    name text not null default '',
    picture text,
    password_hash text,
    invite_hash text unique,
    invite_expires_at timestamptz,
    created_at timestamptz not null default now(),
    last_login_at timestamptz,
    check ((invite_hash is null) = (invite_expires_at is null))
);

create table if not exists forms.sessions (
    key text primary key,
    email text not null references forms.users (email) on delete cascade,
    created_at timestamptz not null default now(),
    expires_at timestamptz not null
);
create index if not exists sessions_email_idx on forms.sessions (email);
create index if not exists sessions_expires_idx on forms.sessions (expires_at);

create table if not exists forms.documents (
    id text primary key,
    template text not null check (template in ('invoice', 'agreement')),
    style text not null check (style in ('classic', 'modern')),
    title text not null,
    data jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists documents_updated_idx on forms.documents (updated_at desc);
"""

_pool: ConnectionPool | None = None
_lock = threading.Lock()


def url() -> str:
    return os.environ.get("DATABASE_URL") or LOCAL_URL


def pool() -> ConnectionPool:
    global _pool
    with _lock:
        if _pool is None:
            _pool = ConnectionPool(
                url(),
                min_size=1,
                max_size=8,
                timeout=10,
                open=True,
                # Neon's pooled endpoint is PgBouncer; server-side prepared
                # statements do not survive its connection hand-offs.
                kwargs={"autocommit": True, "row_factory": dict_row, "prepare_threshold": None},
            )
        return _pool


def close() -> None:
    global _pool
    with _lock:
        if _pool is not None:
            _pool.close()
            _pool = None


def migrate() -> None:
    with pool().connection() as conn:
        conn.execute(SCHEMA)


def rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with pool().connection() as conn:
        return conn.execute(sql, params).fetchall()


def row(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with pool().connection() as conn:
        return conn.execute(sql, params).fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    """Run a statement and return how many rows it touched."""
    with pool().connection() as conn:
        return conn.execute(sql, params).rowcount
