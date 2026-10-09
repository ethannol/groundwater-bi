"""Keep the LookML honest without a Looker instance.

Looker's own validator and Spectacles both need a live instance. These tests
do what can be done offline:

1. every .lkml file parses;
2. every view's sql_table_name is a model dbt actually built;
3. every ${TABLE}.column reference names a real column in that model;
4. every ${view.field} reference in an explore join exists in that view.

The DuckDB file is produced by `dbt build` (see Makefile). If it is missing the
schema tests are skipped rather than failed, so `pytest` still gives a useful
signal on a fresh clone.
"""
from __future__ import annotations

import re
from pathlib import Path

import lkml
import pytest

ROOT = Path(__file__).resolve().parents[1]
LOOKER = ROOT / "looker"
DUCKDB_PATH = ROOT / "warehouse" / "target" / "groundwater.duckdb"

TABLE_REF = re.compile(r"\$\{TABLE\}\.([A-Za-z_][A-Za-z0-9_]*)")
FIELD_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\}")

LKML_FILES = sorted(LOOKER.rglob("*.lkml"))


def _parse(path: Path) -> dict:
    return lkml.load(path.read_text())


@pytest.fixture(scope="session")
def views() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in LOOKER.glob("views/*.view.lkml"):
        for view in _parse(path).get("views", []):
            out[view["name"]] = view
    return out


@pytest.fixture(scope="session")
def warehouse_columns() -> dict[str, set[str]]:
    if not DUCKDB_PATH.exists():
        pytest.skip(f"{DUCKDB_PATH} not built; run `make build` first")
    import duckdb

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    rows = con.execute(
        "select table_schema, table_name, column_name from information_schema.columns"
    ).fetchall()
    con.close()
    cols: dict[str, set[str]] = {}
    for schema, table, col in rows:
        cols.setdefault(f"{schema}.{table}", set()).add(col)
    return cols


def _fields(view: dict) -> set[str]:
    names: set[str] = set()
    for kind in ("dimensions", "measures", "filters", "parameters"):
        names.update(f["name"] for f in view.get(kind, []))
    for group in view.get("dimension_groups", []):
        for tf in group.get("timeframes", []):
            names.add(f"{group['name']}_{tf}")
    return names


@pytest.mark.parametrize("path", LKML_FILES, ids=lambda p: p.relative_to(LOOKER).as_posix())
def test_lookml_parses(path: Path) -> None:
    _parse(path)


def test_model_includes_resolve() -> None:
    model = _parse(LOOKER / "models" / "groundwater.model.lkml")
    includes = model.get("includes") or [model.get("include")]
    for pattern in includes:
        matches = list(LOOKER.glob(pattern.lstrip("/")))
        assert matches, f"include {pattern!r} matches no files"


def test_view_tables_exist(views: dict[str, dict], warehouse_columns: dict[str, set[str]]) -> None:
    for name, view in views.items():
        table = view["sql_table_name"].strip()
        assert table in warehouse_columns, f"view {name}: {table} is not a built dbt model"


def test_table_column_refs_exist(views: dict[str, dict], warehouse_columns: dict[str, set[str]]) -> None:
    problems: list[str] = []
    for name, view in views.items():
        table = view["sql_table_name"].strip()
        cols = warehouse_columns.get(table, set())
        for kind in ("dimensions", "dimension_groups", "measures"):
            for field in view.get(kind, []):
                for key in ("sql", "sql_latitude", "sql_longitude"):
                    for col in TABLE_REF.findall(field.get(key, "")):
                        if col not in cols:
                            problems.append(f"{name}.{field['name']}: {table}.{col} does not exist")
    assert not problems, "\n".join(problems)


def test_explore_join_fields_exist(views: dict[str, dict]) -> None:
    model = _parse(LOOKER / "models" / "groundwater.model.lkml")
    problems: list[str] = []
    for explore in model.get("explores", []):
        base = explore["name"]
        assert base in views, f"explore {base} has no view"
        for join in explore.get("joins", []):
            assert join["name"] in views, f"join {join['name']} has no view"
            for view_name, field in FIELD_REF.findall(join.get("sql_on", "")):
                if view_name not in views or field not in _fields(views[view_name]):
                    problems.append(f"explore {base}: ${{{view_name}.{field}}} not found")
        af = explore.get("access_filter")
        if af:
            view_name, field = af["field"].split(".")
            if field not in _fields(views.get(view_name, {})):
                problems.append(f"explore {base}: access_filter field {af['field']} not found")
    assert not problems, "\n".join(problems)
