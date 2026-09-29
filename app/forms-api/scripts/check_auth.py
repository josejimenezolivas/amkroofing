"""Exercise sign-in and the guard end to end, in process.

    .venv/bin/python scripts/check_auth.py

Creates a throwaway database on the local Postgres (compose.yaml), stubs
Google's token exchange, and drops the database at the end, so it needs no API
server and no Google client, and leaves the real document list alone. Exits
non-zero if any check fails. Needs httpx (pip install httpx).
"""

import os
import secrets
import sys
import threading
import urllib.parse
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402

SERVER = db.url()
if urllib.parse.urlsplit(SERVER).hostname not in ("127.0.0.1", "localhost"):
    raise SystemExit("check_auth creates and drops a database; point it at a local server only.")
SCRATCH = f"amk_auth_check_{secrets.token_hex(4)}"
with psycopg.connect(SERVER, autocommit=True) as admin:
    admin.execute(f"create database {SCRATCH}")
os.environ["DATABASE_URL"] = urllib.parse.urlsplit(SERVER)._replace(path=f"/{SCRATCH}").geturl()
os.environ.pop("GOOGLE_CLIENT_ID", None)
os.environ.pop("GOOGLE_CLIENT_SECRET", None)
db.migrate()

from fastapi.testclient import TestClient  # noqa: E402

from app import accounts, google  # noqa: E402
from app.main import app  # noqa: E402

GOOD = "Slate-Shingle-42"
failures = 0


def check(label: str, ok: bool, detail: object = "") -> None:
    global failures
    print(f"{'ok  ' if ok else 'FAIL'} {label}" + (f"  ({detail})" if not ok and detail else ""))
    failures += not ok


def client(base: str = "http://testserver") -> TestClient:
    # No `with`: the lifespan would start Chromium, and nothing here prints.
    return TestClient(app, base_url=base, follow_redirects=False)


def auth_error(response) -> str:
    query = urllib.parse.urlparse(response.headers.get("location", "")).query
    return urllib.parse.parse_qs(query).get("auth_error", [""])[0]


def invite_signup(c: TestClient, email: str, **overrides) -> object:
    token = accounts.invite(email)
    body = {"email": email, "token": token, "password": GOOD, "name": "Test Roofer", **overrides}
    return c.post("/forms/api/auth/email/signup", json=body)


# --- the guard --------------------------------------------------------------
anon = client()
check("health is public", anon.get("/forms/api/health").status_code == 200)
for method, path in [
    ("GET", "/forms/api/documents"),
    ("GET", "/forms/api/documents/reference-invoice"),
    ("POST", "/forms/api/documents"),
    ("DELETE", "/forms/api/documents/reference-invoice"),
    ("GET", "/forms/api/templates"),
    ("POST", "/forms/api/render/pdf"),
    ("POST", "/forms/api/render/docx"),
    ("GET", "/forms/api/auth/me"),
]:
    status = anon.request(method, path, json={}).status_code
    check(f"{method} {path} needs a session", status == 401, status)
forged = client()
forged.cookies.set("amk_session", "made-up", path="/forms")
check("a made-up session is refused", forged.get("/forms/api/documents").status_code == 401)
check("config reports Google off", anon.get("/forms/api/auth/config").json() == {"google": False})

# --- accepting an invite ----------------------------------------------------
c = client()
email = "crew@amkroofing.com"
token = accounts.invite(email)
wrong = c.post("/forms/api/auth/email/signup", json={"email": email, "token": "nope", "password": GOOD})
check("a wrong invite token is refused", wrong.status_code == 400, wrong.text)
weak = c.post("/forms/api/auth/email/signup", json={"email": email, "token": token, "password": "Password12!"})
check("a weak password is refused", weak.status_code == 400 and "breach" in weak.json()["detail"], weak.text)
personal = c.post("/forms/api/auth/email/signup", json={"email": email, "token": token, "password": "Crew-Member-91"})
check("a password containing the email is refused", personal.status_code == 400, personal.text)
ok = c.post("/forms/api/auth/email/signup", json={"email": email, "token": token, "password": GOOD, "name": "Crew"})
check("a valid invite signs in", ok.status_code == 200 and ok.json()["email"] == email, ok.text)
cookie = ok.headers.get("set-cookie", "").lower()
check(
    "the session cookie is httponly, lax, scoped to /forms, and not secure over http",
    all(part in cookie for part in ("httponly", "samesite=lax", "path=/forms")) and "secure" not in cookie,
    cookie,
)
check("the signed-in user can list documents", c.get("/forms/api/documents").status_code == 200)

# --- documents, for a signed-in user ------------------------------------------
made = c.post("/forms/api/documents", json={"template": "invoice"})
doc = made.json()
check("a document can be created from a template", made.status_code == 201 and doc["data"]["fields"], made.text)
doc["data"]["fields"]["client_name"] = "Jane Roofer"
saved = c.put(f"/forms/api/documents/{doc['id']}", json={"data": doc["data"], "style": "modern"})
check(
    "saving stores the data and the style and moves updated_at",
    saved.status_code == 200
    and saved.json()["style"] == "modern"
    and saved.json()["updated_at"] > doc["updated_at"],
    saved.text,
)
fetched = c.get(f"/forms/api/documents/{doc['id']}").json()
check("the saved data reads back", fetched["data"]["fields"]["client_name"] == "Jane Roofer", fetched)
check("the title follows the client until renamed", fetched["title"].startswith("Jane Roofer"), fetched["title"])
renamed = c.put(f"/forms/api/documents/{doc['id']}", json={"data": fetched["data"], "title": "Talmadge reroof"})
check("a document can be renamed", renamed.json()["title"] == "Talmadge reroof", renamed.text)
fetched["data"]["fields"]["client_name"] = "Jane Q. Roofer"
kept = c.put(f"/forms/api/documents/{doc['id']}", json={"data": fetched["data"]}).json()
check("later saves keep the new name", kept["title"] == "Talmadge reroof", kept["title"])
check("the list puts the latest edit first", c.get("/forms/api/documents").json()[0]["id"] == doc["id"])
check("a document can be deleted", c.delete(f"/forms/api/documents/{doc['id']}").status_code == 204)
check("and is gone", c.get(f"/forms/api/documents/{doc['id']}").status_code == 404)
check("deleting it again is 404", c.delete(f"/forms/api/documents/{doc['id']}").status_code == 404)
check("/me names the user", c.get("/forms/api/auth/me").json()["name"] == "Crew")
again = client().post(
    "/forms/api/auth/email/signup", json={"email": email, "token": token, "password": "Other-Gable-77"}
)
check("an invite link works once", again.status_code == 400, again.text)
stored = accounts.get_user(email)
check("the password is stored as an Argon2id hash", stored.password_hash.startswith("$argon2id$"))
raw_id = c.cookies.get("amk_session")
sessions = db.rows("select * from forms.sessions")
check(
    "the raw session id is not stored anywhere",
    sessions and all(raw_id not in str(s.values()) for s in sessions),
)

racer = "racer@amkroofing.com"
race_token = accounts.invite(racer)
winners: list[object] = []
threads = [
    threading.Thread(target=lambda p=p: winners.append(accounts.accept_invite(racer, race_token, p, "")))
    for p in ("Ridge-Vent-4417", "Soffit-Board-8823")
]
for t in threads:
    t.start()
for t in threads:
    t.join()
check("two requests racing on one invite: exactly one wins", sum(w is not None for w in winners) == 1, winners)

# --- password sign-in -------------------------------------------------------
fresh = client()
bad = fresh.post("/forms/api/auth/email/login", json={"email": email, "password": "Wrong-Pass-00"})
nobody = fresh.post("/forms/api/auth/email/login", json={"email": "who@x.com", "password": GOOD})
check("a wrong password is 401", bad.status_code == 401)
check("an unknown email gets the same answer", nobody.json() == bad.json(), nobody.text)
good = fresh.post("/forms/api/auth/email/login", json={"email": " Crew@AMKroofing.com ", "password": GOOD})
check("the right password signs in, email case-insensitive", good.status_code == 200, good.text)
pending = "pending@amkroofing.com"
accounts.invite(pending)
check(
    "an invited user with no password yet cannot sign in by password",
    client().post("/forms/api/auth/email/login", json={"email": pending, "password": GOOD}).status_code == 401,
)

throttled = client()
codes = [
    throttled.post("/forms/api/auth/email/login", json={"email": pending, "password": f"Guess-{i}-xx"}).status_code
    for i in range(11)
]
check("ten failures in a row lock the address for a while", codes[-1] == 429, codes)

# --- signing out and revocation ---------------------------------------------
check("logout succeeds", fresh.post("/forms/api/auth/logout").status_code == 200)
fresh.cookies.clear()
fresh.cookies.set("amk_session", good.cookies.get("amk_session"), path="/forms")
check("a signed-out session id no longer works", fresh.get("/forms/api/auth/me").status_code == 401)

stale = client()
stale_login = stale.post("/forms/api/auth/email/login", json={"email": email, "password": GOOD})
key = accounts._digest(stale_login.cookies.get("amk_session"))
db.execute("update forms.sessions set expires_at = now() - interval '1 second' where key = %s", (key,))
check("an expired session is refused", stale.get("/forms/api/auth/me").status_code == 401)

check("removing a user succeeds", accounts.remove_user(email))
check("removing a user signs them out everywhere, at once", c.get("/forms/api/documents").status_code == 401)
check(
    "and deletes their sessions",
    db.row("select count(*) as n from forms.sessions where email = %s", (email,))["n"] == 0,
)

# --- Google -----------------------------------------------------------------
start = anon.get("/forms/api/auth/google/start")
check(
    "Google start without a client bounces back with a message",
    start.status_code == 303 and "not set up" in auth_error(start),
    start.headers.get("location"),
)

os.environ["GOOGLE_CLIENT_ID"] = "test-client.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-secret"
check("config reports Google on", anon.get("/forms/api/auth/config").json() == {"google": True})

g = client("https://testserver")
start = g.get(
    "/forms/api/auth/google/start",
    headers={"x-forwarded-proto": "https", "x-forwarded-host": "www.amkroofing.com"},
)
location = urllib.parse.urlparse(start.headers["location"])
params = urllib.parse.parse_qs(location.query)
check("Google start redirects to the account chooser", location.netloc == "accounts.google.com")
check(
    "the redirect URI is the public origin, not the container's",
    params["redirect_uri"] == ["https://www.amkroofing.com/forms/api/auth/google/callback"],
    params.get("redirect_uri"),
)
state = params["state"][0]
check("the state cookie matches the state sent to Google", g.cookies.get("amk_oauth_state") == state)

tampered = g.get("/forms/api/auth/google/callback", params={"code": "c", "state": "other"})
check("a callback with the wrong state is refused", "tampered" in auth_error(tampered), tampered.headers)
cancelled = g.get("/forms/api/auth/google/callback", params={"error": "access_denied"})
check("a cancelled chooser says so", "cancelled" in auth_error(cancelled))

identified = {"email": "stranger@gmail.com"}
google.identify = lambda code, redirect_uri: google.Identity(identified["email"], "Owner", "https://p/x.png")

g.cookies.set("amk_oauth_state", state, path="/forms/api/auth/google")
outsider = g.get("/forms/api/auth/google/callback", params={"code": "c", "state": state})
check("an uninvited Google account is turned away", "not been invited" in auth_error(outsider), auth_error(outsider))
check("and gets no session", g.get("/forms/api/auth/me").status_code == 401)

owner = "owner@amkroofing.com"
accounts.invite(owner)
identified["email"] = "Owner@AMKroofing.com"
g.cookies.set("amk_oauth_state", state, path="/forms/api/auth/google")
landing = g.get("/forms/api/auth/google/callback", params={"code": "c", "state": state})
check("an invited Google account lands in the app", landing.headers.get("location") == "/forms/", landing.headers)
check("the session cookie is secure over https", "secure" in landing.headers.get("set-cookie", "").lower())
me = g.get("/forms/api/auth/me")
check("Google fills in the name and picture", me.status_code == 200 and me.json()["picture"], me.text)
check("signing in with Google spends the pending invite", accounts.get_user(owner).invite_hash is None)

db.close()
with psycopg.connect(SERVER, autocommit=True) as admin:
    admin.execute(f"drop database {SCRATCH} with (force)")

print(f"\n{'All checks passed.' if not failures else f'{failures} check(s) failed.'}")
sys.exit(1 if failures else 0)
