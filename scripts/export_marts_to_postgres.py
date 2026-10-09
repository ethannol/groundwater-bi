"""Copy the dbt marts from DuckDB into a Postgres database.

Works for the local docker-compose Postgres and for a hosted one such as Neon
(set PG_URL with sslmode=require). Hex, Metabase and most BI tools can read
Postgres; none of them read a DuckDB file sitting on your laptop.

Usage:
    PG_URL=postgresql://user:pass@host:5432/db python scripts/export_marts_to_postgres.py
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = ROOT / "warehouse" / "target" / "groundwater.duckdb"
PG_URL = os.environ.get("PG_URL", "postgresql://groundwater:groundwater@localhost:5432/groundwater")
MARTS = ["dim_well", "dim_constituent", "fct_result"]


def main() -> None:
    if not DUCKDB_PATH.exists():
        raise SystemExit(f"{DUCKDB_PATH} not found; run `make build` first")
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{PG_URL}' AS pg (TYPE postgres)")
    for table in MARTS:
        con.execute(f"DROP TABLE IF EXISTS pg.public.{table}")
        con.execute(f"CREATE TABLE pg.public.{table} AS SELECT * FROM main.{table}")
        n = con.execute(f"SELECT count(*) FROM pg.public.{table}").fetchone()[0]
        print(f"{table}: {n} rows")
    con.close()


if __name__ == "__main__":
    main()
