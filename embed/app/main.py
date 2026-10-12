"""Host application for the embedded-analytics demo.

This is the only piece of code a product team would own when embedding a BI
tool: it decides who the viewer is, what they may see, and mints a signed URL
that encodes exactly that. The BI tool renders the dashboard; it never learns
anything about the viewer beyond the locked parameters in the token.

The pattern is the same for Metabase static embedding (used here because it
is free) and Looker SSO embedding (signed URL with user attributes). Only the
payload shape and the signing details differ. See docs/adr/0002.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SITE_URL = os.environ.get("METABASE_SITE_URL", "http://localhost:3000").rstrip("/")
SECRET_KEY = os.environ.get("METABASE_SECRET_KEY", "")
DASHBOARD_ID = int(os.environ.get("METABASE_DASHBOARD_ID", "1"))
TOKEN_TTL = int(os.environ.get("EMBED_TOKEN_TTL", "600"))

# Demo tenant registry: tenant slug -> HUC-8 watershed the tenant may see.
# In a real product this mapping comes from the authenticated session, never
# from the request. Codes are the four largest watersheds in the snapshot.
TENANTS: dict[str, str] = {
    "mojave": "18090208",
    "antelope-fremont": "18090207",
    "santa-ana": "18070203",
    "lower-colorado": "18100100",
}

app = FastAPI(title="groundwater-bi embed host")
bearer = HTTPBearer(auto_error=False)
SESSION_TTL = 900


@app.middleware("http")
async def prevent_authenticated_response_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


def demo_users() -> dict:
    """Server-side demo registry. Empty by default: no anonymous tenant access."""
    try:
        users = json.loads(os.environ.get("DEMO_USERS_JSON", "{}"))
        if not isinstance(users, dict) or not all(
            isinstance(subject, str)
            and isinstance(user, dict)
            and isinstance(user.get("token"), str)
            and isinstance(user.get("tenants"), list)
            and all(isinstance(tenant, str) for tenant in user["tenants"])
            for subject, user in users.items()
        ):
            raise ValueError("registry must be an object")
        return users
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=503, detail="demo identity configuration invalid"
        )


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    users = demo_users()
    if credentials:
        for subject, user in users.items():
            configured = user.get("token", "")
            if configured and secrets.compare_digest(
                credentials.credentials.encode(), configured.encode()
            ):
                return subject
        raise HTTPException(
            status_code=401,
            detail="invalid bearer credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session = request.cookies.get("groundwater_session")
    session_secret = os.environ.get("DEMO_SESSION_SECRET", "")
    if session and session_secret:
        try:
            claims = jwt.decode(
                session,
                session_secret,
                algorithms=["HS256"],
                audience="groundwater-bi-host",
                issuer="groundwater-bi-demo",
                options={"require": ["sub", "iat", "exp", "aud", "iss"]},
            )
            if claims["sub"] in users:
                return claims["sub"]
        except jwt.InvalidTokenError:
            pass
    raise HTTPException(
        status_code=401,
        detail="authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authorize_tenant(tenant: str, subject: str) -> None:
    # Authorization is resolved from identity on every request, including
    # existing sessions, so registry revocation stops new embed URLs.
    if tenant not in demo_users().get(subject, {}).get("tenants", []):
        raise HTTPException(status_code=403, detail="tenant access denied")
    if tenant not in TENANTS:
        raise HTTPException(status_code=404, detail="unknown tenant")


@app.post("/session")
def session(subject: str = Depends(current_user)) -> JSONResponse:
    """Exchange a demo bearer credential for a short-lived HttpOnly host session."""
    session_secret = os.environ.get("DEMO_SESSION_SECRET", "")
    if not session_secret:
        raise HTTPException(
            status_code=503, detail="demo session signing is not configured"
        )
    now = int(time.time())
    value = jwt.encode(
        {
            "sub": subject,
            "iat": now,
            "exp": now + SESSION_TTL,
            "aud": "groundwater-bi-host",
            "iss": "groundwater-bi-demo",
        },
        session_secret,
        algorithm="HS256",
    )
    response = JSONResponse({"user": subject})
    response.set_cookie(
        "groundwater_session",
        value,
        max_age=SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("DEMO_COOKIE_SECURE", "true").lower() == "true",
    )
    return response


def mint_embed_url(tenant: str, now: float | None = None) -> str:
    """Return a Metabase static-embed URL scoped to one tenant's watershed."""
    if tenant not in TENANTS:
        raise KeyError(tenant)
    if not SECRET_KEY:
        raise RuntimeError("METABASE_SECRET_KEY is not set")
    issued = int(now if now is not None else time.time())
    payload = {
        "resource": {"dashboard": DASHBOARD_ID},
        # Locked parameters: the viewer cannot change these from the iframe.
        "params": {"huc8": TENANTS[tenant]},
        "iat": issued,
        "exp": issued + TOKEN_TTL,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return f"{SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"


@app.get("/", response_class=HTMLResponse)
def index(subject: str = Depends(current_user)) -> str:
    links = "".join(
        f'<li><a href="/dashboard/{slug}">{slug}</a> &rarr; HUC-8 {huc8}</li>'
        for slug, huc8 in TENANTS.items()
        if slug in demo_users().get(subject, {}).get("tenants", [])
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>groundwater-bi embed demo</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:2rem auto">
<h1>Your watersheds</h1>
<p>Each link mints a signed, short-lived embed URL locked to one watershed.</p>
<ul>{links}</ul></body></html>"""


@app.get("/dashboard/{tenant}", response_class=HTMLResponse)
def dashboard(tenant: str, subject: str = Depends(current_user)) -> str:
    authorize_tenant(tenant, subject)
    try:
        url = mint_embed_url(tenant)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown tenant")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{tenant} · groundwater-bi</title></head>
<body style="margin:0">
<iframe src="{url}" frameborder="0" width="100%" height="900" allowtransparency></iframe>
</body></html>"""


@app.get("/token/{tenant}")
def token(tenant: str, subject: str = Depends(current_user)) -> JSONResponse:
    """Expose the minted URL as JSON so it can be tested without a browser."""
    authorize_tenant(tenant, subject)
    try:
        return JSONResponse({"tenant": tenant, "embed_url": mint_embed_url(tenant)})
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown tenant")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
