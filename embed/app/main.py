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

import os
import time

import jwt
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

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
def index() -> str:
    links = "".join(
        f'<li><a href="/dashboard/{slug}">{slug}</a> &rarr; HUC-8 {huc8}</li>'
        for slug, huc8 in TENANTS.items()
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>groundwater-bi embed demo</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:2rem auto">
<h1>Pick a tenant</h1>
<p>Each link mints a signed, short-lived embed URL locked to one watershed.</p>
<ul>{links}</ul></body></html>"""


@app.get("/dashboard/{tenant}", response_class=HTMLResponse)
def dashboard(tenant: str) -> str:
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
def token(tenant: str) -> JSONResponse:
    """Expose the minted URL as JSON so it can be tested without a browser."""
    try:
        return JSONResponse({"tenant": tenant, "embed_url": mint_embed_url(tenant)})
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown tenant")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
