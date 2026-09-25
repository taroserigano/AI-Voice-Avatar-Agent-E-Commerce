"""Production sign-in through an OIDC provider (Amazon Cognito in the cloud).

Authorization-code flow with PKCE, state, and nonce. The transient values ride in a signed,
short-lived cookie so no server-side state is needed between start and callback.

Status: written against the OIDC spec and Cognito's documented endpoints, but NOT yet run
against a live Cognito user pool. Local development uses the development adapter.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from commerce.config import Settings

STATE_COOKIE = "ac_oidc"
STATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class OidcClaims:
    subject: str
    email: str
    name: str


class OidcError(Exception):
    pass


@lru_cache(maxsize=4)
def _discovery(issuer: str) -> dict[str, Any]:
    resp = httpx.get(f"{issuer.rstrip('/')}/.well-known/openid-configuration", timeout=5)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    return data


@lru_cache(maxsize=4)
def _jwks_client(jwks_uri: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_uri)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(payload: dict[str, Any], secret: str) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    mac = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{mac}"


def _unsign(value: str, secret: str) -> dict[str, Any]:
    try:
        body, mac = value.split(".", 1)
    except ValueError as exc:
        raise OidcError("malformed state cookie") from exc
    expected = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(mac, expected):
        raise OidcError("state cookie signature mismatch")
    payload: dict[str, Any] = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    if payload.get("exp", 0) < time.time():
        raise OidcError("sign-in attempt expired")
    return payload


def _require(settings: Settings) -> tuple[str, str, str]:
    if not (settings.oidc_issuer and settings.oidc_client_id and settings.oidc_redirect_uri):
        raise OidcError("OIDC is not configured (OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_REDIRECT_URI)")
    return settings.oidc_issuer, settings.oidc_client_id, settings.oidc_redirect_uri


def build_authorization_redirect(settings: Settings, return_to: str) -> tuple[str, str]:
    """Return (provider URL to redirect to, signed state cookie value)."""
    issuer, client_id, redirect_uri = _require(settings)
    verifier = secrets.token_urlsafe(48)
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    challenge = _b64(hashlib.sha256(verifier.encode()).digest())
    cookie = _sign(
        {
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
            "return_to": return_to,
            "exp": int(time.time()) + STATE_TTL_SECONDS,
        },
        settings.session_secret,
    )
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{_discovery(issuer)['authorization_endpoint']}?{urlencode(params)}"
    return url, cookie


def complete_authorization(
    settings: Settings, *, code: str, state: str, state_cookie: str
) -> tuple[OidcClaims, str]:
    """Exchange the code, verify the ID token, and return (claims, return_to)."""
    issuer, client_id, redirect_uri = _require(settings)
    saved = _unsign(state_cookie, settings.session_secret)
    if not hmac.compare_digest(saved["state"], state):
        raise OidcError("state mismatch")
    meta = _discovery(issuer)
    auth = (client_id, settings.oidc_client_secret) if settings.oidc_client_secret else None
    resp = httpx.post(
        meta["token_endpoint"],
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": saved["verifier"],
        },
        auth=auth,
        timeout=10,
    )
    if resp.status_code != 200:
        raise OidcError(f"token exchange failed with HTTP {resp.status_code}")
    id_token = resp.json().get("id_token")
    if not id_token:
        raise OidcError("no id_token in token response")
    key = _jwks_client(meta["jwks_uri"]).get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        key.key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=issuer,
    )
    if claims.get("nonce") != saved["nonce"]:
        raise OidcError("nonce mismatch")
    email = claims.get("email")
    if not email or claims.get("email_verified") is False:
        raise OidcError("provider did not return a verified email")
    return (
        OidcClaims(subject=claims["sub"], email=email, name=claims.get("name") or email),
        saved["return_to"],
    )
