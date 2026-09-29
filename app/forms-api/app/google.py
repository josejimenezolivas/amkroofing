"""Sign in with Google: the browser is sent to Google's account chooser and
comes back to /forms/api/auth/google/callback with a code we trade for the
person's verified email. Google proves who they are; whether they may come in
is still the invite list's call.

Off until GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set. A "Web
application" client cannot trade a code without its secret.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


class GoogleError(Exception):
    """A failed sign-in, worded for the person looking at the login page."""


@dataclass
class Identity:
    email: str
    name: str | None
    picture: str | None


def _client() -> tuple[str, str] | None:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    return (client_id, secret) if client_id and secret else None


def enabled() -> bool:
    return _client() is not None


def authorize_url(redirect_uri: str, state: str) -> str:
    client = _client()
    if client is None:
        raise GoogleError("Google sign-in is not set up on this server.")
    params = {
        "client_id": client[0],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"


def _claims(id_token: str) -> dict:
    try:
        payload = id_token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError) as exc:
        raise GoogleError("Google returned an unreadable identity token.") from exc


def identify(code: str, redirect_uri: str) -> Identity:
    """Trade the callback's code for the person it belongs to."""
    client = _client()
    if client is None:
        raise GoogleError("Google sign-in is not set up on this server.")
    client_id, secret = client
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    request = urllib.request.Request(TOKEN_ENDPOINT, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            token = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise GoogleError("Google rejected the sign-in. Try again.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GoogleError("Could not reach Google to finish signing in.") from exc

    id_token = token.get("id_token")
    if not id_token:
        raise GoogleError("Google returned no identity token.")

    # The token came straight from Google's token endpoint over TLS, in exchange
    # for our client secret, so OpenID Connect Core 3.1.3.7 lets TLS stand in for
    # the signature. The audience, issuer and expiry still have to be ours.
    claims = _claims(id_token)
    if claims.get("aud") != client_id or claims.get("iss") not in ISSUERS:
        raise GoogleError("That identity token was not issued for AMK Roofing Forms.")
    if float(claims.get("exp", 0)) < time.time():
        raise GoogleError("Google sign-in expired. Try again.")
    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleError("Your Google account has no verified email address.")
    return Identity(email=claims["email"], name=claims.get("name"), picture=claims.get("picture"))
