"""Execute the consumer metric contracts on censored synthetic data, no browsers."""

from pathlib import Path

import duckdb
import lkml
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_mart_and_consumer_metrics_exclude_limits_from_concentration_summary():
    con = duckdb.connect()
    # A high non-detect limit would radically distort the median if treated as
    # a measurement. DNQ is not a quantified measurement; a true detection
    # remains valid when its reporting limit is absent.
    con.execute("""
        create table stg_samples as
        select 'r' || row_number() over () as result_id, 'well' as site_id,
               'arsenic' as family, 'Arsenic' as characteristic, 'Dissolved' as fraction,
               'ug/L' as unit, 'activity' as activity_id, 'Sample-Routine' as activity_type,
               date '2020-01-01' as sample_date, 'method' as method_id,
               value, 0.0 as lower_bound, value as upper_bound,
               value as detection_limit, is_censored, is_dnq,
               false as is_estimated, is_dl_missing
        from (values
            (2.0, false, false, false), (4.0, false, false, false),
            (100.0, true, false, false), (200.0, false, true, false),
            (300.0, false, false, true)
        ) t(value, is_censored, is_dnq, is_dl_missing)
    """)
    mart = (ROOT / "warehouse/models/marts/fct_result.sql").read_text()
    con.execute(
        "create table fct_result as "
        + mart.replace("{{ ref('stg_samples') }}", "stg_samples")
    )
    con.execute(
        """create table dim_constituent as select distinct constituent_key,
           'arsenic' as family, 'Arsenic' as characteristic,
           'Dissolved' as fraction, 'ug/L' as unit from fct_result"""
    )
    assert con.execute(
        "select detected_value from fct_result order by value"
    ).fetchall() == [(2.0,), (4.0,), (None,), (None,), (300.0,)]
    row = con.execute((ROOT / "hex/metrics.sql").read_text()).fetchone()
    assert row == ("arsenic", "Arsenic", "Dissolved", "ug/L", 2020, 5, 1, 1, 0.2, 4.0)
    # The LookML defaults use the same safe mart column, not raw value.
    view = lkml.load((ROOT / "looker/views/fct_result.view.lkml").read_text())["views"][
        0
    ]
    measures = {m["name"]: m for m in view["measures"]}
    dims = {d["name"]: d for d in view["dimensions"]}
    assert dims["value"]["hidden"] == "yes"
    looker_column = dims["detected_value"]["sql"].replace("${TABLE}.", "").strip()
    assert measures["median_detected_value"]["sql"].strip() == "${detected_value}"
    assert (
        con.execute(f"select median({looker_column}) from fct_result").fetchone()[0]
        == 4.0
    )
    schema = yaml.safe_load((ROOT / "warehouse/models/marts/schema.yml").read_text())
    fact = next(m for m in schema["models"] if m["name"] == "fct_result")
    columns = {c["name"]: c for c in fact["columns"]}
    assert columns["value"]["meta"]["dimension"]["hidden"] is True
    assert "metrics" not in columns["value"]["meta"]
    assert (
        columns["detected_value"]["meta"]["metrics"]["median_detected_value"]["type"]
        == "median"
    )
    con.close()


def test_all_censored_group_has_no_detected_median():
    con = duckdb.connect()
    con.execute(
        "create table fct_result(result_id varchar, well_key varchar, constituent_key varchar, sample_year int, censored_flag int, detected_value double)"
    )
    con.execute(
        "insert into fct_result values ('r1', 'w1', 'a', 2020, 1, null), ('r2', 'w2', 'a', 2020, 1, null)"
    )
    con.execute("""create table dim_constituent(constituent_key varchar, family varchar,
                   characteristic varchar, fraction varchar, unit varchar)""")
    con.execute("""insert into dim_constituent values
                   ('a', 'arsenic', 'Arsenic', 'Dissolved', 'ug/L'),
                   ('a-total', 'arsenic', 'Arsenic', 'Total', 'ug/L')""")
    # A detected total-fraction result must not supply a median for the
    # all-censored dissolved group, even though their family/year match.
    con.execute("insert into fct_result values ('r3', 'w3', 'a-total', 2020, 0, 99)")
    assert con.execute((ROOT / "hex/metrics.sql").read_text()).fetchall() == [
        ("arsenic", "Arsenic", "Dissolved", "ug/L", 2020, 2, 2, 2, 1.0, None),
        ("arsenic", "Arsenic", "Total", "ug/L", 2020, 1, 1, 0, 0.0, 99.0),
    ]
    con.close()
