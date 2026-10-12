"""The embed host must lock the tenant's watershed into the signed token."""

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("METABASE_SECRET_KEY", "test-metabase-secret-at-least-32-bytes")
os.environ.setdefault("METABASE_DASHBOARD_ID", "7")

import jwt
from fastapi.testclient import TestClient

from embed.app import main

client = TestClient(main.app)
AUTH = {"Authorization": "Bearer alice-demo"}


@pytest.fixture(autouse=True)
def identity_registry(monkeypatch):
    monkeypatch.setenv(
        "DEMO_USERS_JSON",
        json.dumps(
            {
                "alice": {"token": "alice-demo", "tenants": ["santa-ana"]},
                "bob": {"token": "bob-demo", "tenants": ["mojave"]},
            }
        ),
    )
    monkeypatch.setenv(
        "DEMO_SESSION_SECRET", "test-host-session-secret-at-least-32-bytes"
    )
    client.cookies.clear()


def test_token_locks_tenant_watershed() -> None:
    resp = client.get("/token/santa-ana", headers=AUTH)
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    url = resp.json()["embed_url"]
    token = url.split("/embed/dashboard/")[1].split("#")[0]
    payload = jwt.decode(token, main.SECRET_KEY, algorithms=["HS256"])
    assert payload["resource"] == {"dashboard": 7}
    assert payload["params"] == {"huc8": "18070203"}
    assert payload["exp"] - payload["iat"] == main.TOKEN_TTL


def test_unknown_tenant_is_rejected() -> None:
    assert client.get("/token/nope", headers=AUTH).status_code == 403
    assert client.get("/dashboard/nope", headers=AUTH).status_code == 403


def test_tenant_codes_exist_in_warehouse() -> None:
    """Every demo tenant must map to a watershed that is actually in dim_well."""
    import pytest

    db = (
        Path(main.__file__).resolve().parents[2]
        / "warehouse"
        / "target"
        / "groundwater.duckdb"
    )
    if not db.exists():
        pytest.skip("warehouse not built")
    import duckdb

    con = duckdb.connect(str(db), read_only=True)
    codes = {r[0] for r in con.execute("select distinct huc8 from dim_well").fetchall()}
    con.close()
    assert set(main.TENANTS.values()) <= codes


@pytest.mark.parametrize("path", ["/", "/token/santa-ana", "/dashboard/santa-ana"])
def test_anonymous_requests_cannot_mint_or_view(path):
    assert client.get(path).status_code == 401
    assert (
        client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
    )


def test_authenticated_principal_cannot_select_another_tenant():
    for route in ["token", "dashboard"]:
        denied = client.get(f"/{route}/mojave", headers=AUTH)
        assert denied.status_code == 403
        assert "embed_url" not in denied.text
    allowed = client.get("/token/mojave", headers={"Authorization": "Bearer bob-demo"})
    assert allowed.status_code == 200
    index = client.get("/", headers=AUTH).text
    assert "/dashboard/santa-ana" in index and "/dashboard/mojave" not in index


def test_host_session_cookie_and_revocation(monkeypatch):
    with TestClient(main.app, base_url="https://testserver") as session_client:
        response = session_client.post("/session", headers=AUTH)
        assert response.status_code == 200
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "Secure" in response.headers["set-cookie"]
        assert session_client.get("/token/santa-ana").status_code == 200
        assert session_client.get("/token/mojave").status_code == 403
        monkeypatch.setenv("DEMO_USERS_JSON", "{}")
        assert session_client.get("/token/santa-ana").status_code == 401


def test_tampered_or_expired_session_is_rejected():
    now = int(main.time.time())
    for expiry in [now - 1, now + 60]:
        secret = (
            os.environ["DEMO_SESSION_SECRET"]
            if expiry < now
            else "wrong-session-secret-at-least-32-bytes"
        )
        value = jwt.encode(
            {
                "sub": "alice",
                "iat": now - 60,
                "exp": expiry,
                "aud": "groundwater-bi-host",
                "iss": "groundwater-bi-demo",
            },
            secret,
            algorithm="HS256",
        )
        with TestClient(main.app) as session_client:
            session_client.cookies.set("groundwater_session", value)
            assert session_client.get("/token/santa-ana").status_code == 401
