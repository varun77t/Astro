"""Who is calling: a verified Supabase user, or an anonymous visitor (by IP).

Supabase signs access tokens with an asymmetric key (ES256) and publishes the public half
at /auth/v1/.well-known/jwks.json, so verifying a token needs no secret here. Accounts are
optional: the chart works without one; signing in only raises the daily allowance.
"""

from dataclasses import dataclass
from functools import cache

import jwt
from fastapi import Request

from app.core.config import settings


@dataclass(frozen=True)
class Caller:
    key: str  # "user:<uuid>" or "ip:<address>", what rate limits count against
    user_id: str | None


@cache
def _jwks_client() -> jwt.PyJWKClient | None:
    if not settings.supabase_url:
        return None
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)


def verify_token(token: str, client: jwt.PyJWKClient | None = None) -> str | None:
    """The user id in a valid Supabase access token, or None if it doesn't check out."""
    client = client or _jwks_client()
    if client is None:
        return None
    try:
        key = client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
    except (jwt.PyJWTError, jwt.PyJWKClientError):
        return None
    return claims.get("sub")


def caller(request: Request) -> Caller:
    """FastAPI dependency. A bad or expired token counts as anonymous rather than failing:
    nothing here needs an account, so the worst case is the lower allowance."""
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        user_id = verify_token(header[7:].strip())
        if user_id:
            return Caller(f"user:{user_id}", user_id)
    ip = request.client.host if request.client else "unknown"
    return Caller(f"ip:{ip}", None)
