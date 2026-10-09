"""The embed host must lock the tenant's watershed into the signed token."""
import os
from pathlib import Path

os.environ.setdefault("METABASE_SECRET_KEY", "test-secret")
os.environ.setdefault("METABASE_DASHBOARD_ID", "7")

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from embed.app import main  # noqa: E402

client = TestClient(main.app)


def test_token_locks_tenant_watershed() -> None:
    resp = client.get("/token/santa-ana")
    assert resp.status_code == 200
    url = resp.json()["embed_url"]
    token = url.split("/embed/dashboard/")[1].split("#")[0]
    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert payload["resource"] == {"dashboard": 7}
    assert payload["params"] == {"huc8": "18070203"}
    assert payload["exp"] - payload["iat"] == main.TOKEN_TTL


def test_unknown_tenant_is_rejected() -> None:
    assert client.get("/token/nope").status_code == 404
    assert client.get("/dashboard/nope").status_code == 404


def test_tenant_codes_exist_in_warehouse() -> None:
    """Every demo tenant must map to a watershed that is actually in dim_well."""
    import pytest

    db = Path(main.__file__).resolve().parents[2] / "warehouse" / "target" / "groundwater.duckdb"
    if not db.exists():
        pytest.skip("warehouse not built")
    import duckdb

    con = duckdb.connect(str(db), read_only=True)
    codes = {r[0] for r in con.execute("select distinct huc8 from dim_well").fetchall()}
    con.close()
    assert set(main.TENANTS.values()) <= codes
