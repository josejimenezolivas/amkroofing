"""Who may use the forms, and who is signed in right now.

The forms are invite-only. An invite is a user row with no way in yet: the
person either signs in with Google under the invited address, or opens the
invite link and chooses a password. Re-inviting someone issues a fresh link,
which is also how a forgotten password is reset.

Sessions are opaque random ids kept server-side, so signing out, or removing a
user, revokes access instead of waiting for a token to expire. Only a hash of
the id is stored; the raw id lives in the browser's cookie and nowhere else.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Cookie, HTTPException
from pydantic import BaseModel

from . import db

SESSION_COOKIE = "amk_session"
SESSION_TTL = timedelta(days=30)
INVITE_TTL = timedelta(days=7)

_EMAIL = re.compile(r"[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)+")

# Argon2id with the library defaults (64 MiB, 3 passes), the OWASP minimum.
_hasher = PasswordHasher()
# Verified against when the email is unknown, so a miss costs as long as a hit.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


class User(BaseModel):
    email: str
    name: str = ""
    picture: str | None = None
    password_hash: str | None = None
    invite_hash: str | None = None
    invite_expires_at: datetime | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class Account(BaseModel):
    """What the browser is told about the signed-in user."""

    email: str
    name: str
    picture: str | None = None


def _digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _user(found: dict | None) -> User | None:
    return User.model_validate(found) if found else None


def normalize_email(raw: str) -> str | None:
    email = raw.strip().lower()
    return email if len(email) <= 254 and _EMAIL.fullmatch(email) else None


def account(user: User) -> Account:
    return Account(email=user.email, name=user.name or user.email.split("@")[0], picture=user.picture)


# --- Users ------------------------------------------------------------------


def get_user(email: str) -> User | None:
    return _user(db.row("select * from forms.users where email = %s", (email,)))


def list_users() -> list[User]:
    return [User.model_validate(r) for r in db.rows("select * from forms.users order by email")]


def invite(email: str) -> str:
    """Create the user if needed and return a fresh invite token.

    Any earlier link for this address stops working. An existing password keeps
    working until the new link is used to replace it.
    """
    token = secrets.token_urlsafe(32)
    db.execute(
        "insert into forms.users (email, invite_hash, invite_expires_at)"
        " values (%s, %s, now() + %s)"
        " on conflict (email) do update"
        " set invite_hash = excluded.invite_hash, invite_expires_at = excluded.invite_expires_at",
        (email, _digest(token), INVITE_TTL),
    )
    return token


def remove_user(email: str) -> bool:
    """Delete the user; their sessions go with them."""
    return db.execute("delete from forms.users where email = %s", (email,)) > 0


def invite_is_valid(email: str, token: str) -> bool:
    return (
        db.row(
            "select 1 from forms.users"
            " where email = %s and invite_hash = %s and invite_expires_at > now()",
            (email, _digest(token)),
        )
        is not None
    )


def accept_invite(email: str, token: str, password: str, name: str) -> User | None:
    """Set the password and spend the invite in one statement, so a link can
    only ever be used once, even by two requests racing each other."""
    return _user(
        db.row(
            "update forms.users"
            " set password_hash = %s, name = coalesce(nullif(%s::text, ''), name),"
            "     invite_hash = null, invite_expires_at = null, last_login_at = now()"
            " where email = %s and invite_hash = %s and invite_expires_at > now()"
            " returning *",
            (_hasher.hash(password), name, email, _digest(token)),
        )
    )


def check_password(email: str, password: str) -> User | None:
    user = get_user(email)
    stored = user.password_hash if user else None
    try:
        _hasher.verify(stored or _DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return None
    return user if stored else None


def record_login(
    email: str, *, name: str | None = None, picture: str | None = None, spend_invite: bool = False
) -> User | None:
    """Stamp the sign-in, fill in a missing name and any new picture, and for a
    Google sign-in spend a pending invite link: the person is already in."""
    return _user(
        db.row(
            "update forms.users"
            " set last_login_at = now(),"
            "     name = case when name = '' then coalesce(%s::text, name) else name end,"
            "     picture = coalesce(%s::text, picture),"
            "     invite_hash = case when %s::boolean then null else invite_hash end,"
            "     invite_expires_at = case when %s::boolean then null else invite_expires_at end"
            " where email = %s returning *",
            (name, picture, spend_invite, spend_invite, email),
        )
    )


# --- Sessions ---------------------------------------------------------------


def start_session(email: str) -> str:
    """Store a new session and return the raw id for the cookie."""
    session_id = secrets.token_urlsafe(32)
    db.execute("delete from forms.sessions where expires_at < now()")
    db.execute(
        "insert into forms.sessions (key, email, expires_at) values (%s, %s, now() + %s)",
        (_digest(session_id), email, SESSION_TTL),
    )
    return session_id


def end_session(session_id: str) -> None:
    db.execute("delete from forms.sessions where key = %s", (_digest(session_id),))


def session_user(session_id: str) -> User | None:
    return _user(
        db.row(
            "select u.* from forms.sessions s join forms.users u using (email)"
            " where s.key = %s and s.expires_at > now()",
            (_digest(session_id),),
        )
    )


async def current_user(amk_session: str | None = Cookie(default=None)) -> User:
    """Attach to every route that shows or changes a document."""
    if not amk_session:
        raise HTTPException(status_code=401, detail="Not signed in")
    user = session_user(amk_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Your session has ended. Sign in again.")
    return user


# --- Throttle ---------------------------------------------------------------

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 10


class LoginThrottle:
    """Failed password attempts per email, per instance.

    In memory, so each instance keeps its own count and a cold start resets it.
    It slows down guessing at one account; it is not a distributed limiter.
    """

    def __init__(self) -> None:
        self.failures: dict[str, list[float]] = {}
        self.lock = threading.Lock()

    def retry_after(self, email: str) -> int | None:
        now = time.monotonic()
        with self.lock:
            recent = [t for t in self.failures.get(email, []) if now - t < LOGIN_WINDOW_SECONDS]
            self.failures[email] = recent
            if len(recent) < LOGIN_MAX_FAILURES:
                return None
            return max(1, int(LOGIN_WINDOW_SECONDS - (now - recent[0])))

    def failed(self, email: str) -> None:
        with self.lock:
            self.failures.setdefault(email, []).append(time.monotonic())

    def succeeded(self, email: str) -> None:
        with self.lock:
            self.failures.pop(email, None)


login_throttle = LoginThrottle()
