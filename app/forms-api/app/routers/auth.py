import secrets
import urllib.parse

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .. import accounts, google, password
from ..accounts import SESSION_COOKIE, SESSION_TTL, Account, User, current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

APP_PATH = "/forms/"

# Carries the CSRF nonce across the trip to Google. Lax, not strict: the way
# back is a top-level navigation from accounts.google.com, and strict would
# withhold the cookie exactly then.
STATE_COOKIE = "amk_oauth_state"
STATE_PATH = "/forms/api/auth/google"
STATE_TTL = 600


class EmailLogin(BaseModel):
    email: str
    password: str


class InviteSignup(BaseModel):
    email: str
    token: str
    password: str
    name: str = ""


class AuthConfig(BaseModel):
    google: bool


def _origin(request: Request) -> str:
    """The origin the browser sees. Vercel and both dev proxies name it in
    X-Forwarded-*; the Host header here is the proxy's upstream."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto.split(',')[0].strip()}://{host.split(',')[0].strip()}"


def _secure(request: Request) -> bool:
    return _origin(request).startswith("https://")


def _callback_url(request: Request) -> str:
    return f"{_origin(request)}{STATE_PATH}/callback"


def _sign_in(user: User, request: Request, response: Response) -> Account:
    response.set_cookie(
        SESSION_COOKIE,
        accounts.start_session(user.email),
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=_secure(request),
        samesite="lax",
        path="/forms",
    )
    return accounts.account(user)


@router.get("/config", response_model=AuthConfig)
def config() -> AuthConfig:
    return AuthConfig(google=google.enabled())


@router.get("/me", response_model=Account)
def me(user: User = Depends(current_user)) -> Account:
    return accounts.account(user)


@router.post("/email/login", response_model=Account)
def login(body: EmailLogin, request: Request, response: Response) -> Account:
    email = accounts.normalize_email(body.email) or body.email.strip().lower()
    wait = accounts.login_throttle.retry_after(email)
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again in a few minutes.",
            headers={"Retry-After": str(wait)},
        )
    # One answer for "no such user", "no password yet" and "wrong password":
    # anything more specific confirms which addresses have been invited.
    user = accounts.check_password(email, body.password)
    if user is None:
        accounts.login_throttle.failed(email)
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    accounts.login_throttle.succeeded(email)
    accounts.record_login(user.email)
    return _sign_in(user, request, response)


INVALID_INVITE = "This invite link is invalid or has expired. Ask for a new one."


@router.post("/email/signup", response_model=Account)
def signup(body: InviteSignup, request: Request, response: Response) -> Account:
    """Accept an invite by choosing a password."""
    email = accounts.normalize_email(body.email)
    # Checked before the password, so a dead link is not reported as a weak password.
    if email is None or not accounts.invite_is_valid(email, body.token):
        raise HTTPException(status_code=400, detail=INVALID_INVITE)
    name = body.name.strip()[:120]
    problem = password.problem(body.password, email=email, name=name)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    user = accounts.accept_invite(email, body.token, body.password, name)
    if user is None:
        raise HTTPException(status_code=400, detail=INVALID_INVITE)
    return _sign_in(user, request, response)


@router.post("/logout")
def logout(response: Response, amk_session: str | None = Cookie(default=None)) -> dict[str, bool]:
    if amk_session:
        accounts.end_session(amk_session)
    response.delete_cookie(SESSION_COOKIE, path="/forms")
    return {"ok": True}


def _back_to_app(error: str | None = None) -> RedirectResponse:
    query = f"?{urllib.parse.urlencode({'auth_error': error})}" if error else ""
    response = RedirectResponse(f"{APP_PATH}{query}", status_code=303)
    response.delete_cookie(STATE_COOKIE, path=STATE_PATH)
    return response


@router.get("/google/start")
def google_start(request: Request) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    try:
        url = google.authorize_url(_callback_url(request), state)
    except google.GoogleError as exc:
        return _back_to_app(str(exc))
    response = RedirectResponse(url, status_code=303)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=STATE_TTL,
        httponly=True,
        secure=_secure(request),
        samesite="lax",
        path=STATE_PATH,
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    amk_oauth_state: str | None = Cookie(default=None),
) -> RedirectResponse:
    if error:
        return _back_to_app("Google sign-in was cancelled.")
    # Without this check anyone could hand us a code for their own Google
    # account and sign the visitor in as them.
    if not state or not amk_oauth_state or not secrets.compare_digest(state, amk_oauth_state):
        return _back_to_app("Google sign-in expired or was tampered with. Try again.")
    if not code:
        return _back_to_app("Google did not return an authorization code.")

    try:
        identity = google.identify(code, _callback_url(request))
    except google.GoogleError as exc:
        return _back_to_app(str(exc))

    email = accounts.normalize_email(identity.email) or identity.email.lower()
    user = accounts.record_login(email, name=identity.name, picture=identity.picture, spend_invite=True)
    if user is None:
        return _back_to_app(
            f"{email} has not been invited to AMK Roofing Forms. Ask for an invite, then try again."
        )

    landing = _back_to_app()
    _sign_in(user, request, landing)
    return landing
