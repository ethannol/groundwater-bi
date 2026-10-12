# groundwater-bi

A small, end-to-end metrics stack over public groundwater chemistry data.
One warehouse with censoring-safe default metrics, an offline-validated
LookML explore and an authenticated tenant-scoped embed host. The Hex app is
planned; its SQL contract and setup notes are included, but no live app or
notebook export is claimed.

It exists to back up a specific opinion about deploying BI tooling, written
up in [docs/deployment-opinion.md](docs/deployment-opinion.md): metric
definitions belong in git and get validated in CI, tools are chosen per
audience, and authorization is decided by the application and enforced by
a signed token.

```
data/seed/wqp_samples.csv        public-domain USGS snapshot (never edited)
        │
        ▼
warehouse/  dbt + DuckDB         stg_samples → dim_well, dim_constituent, fct_result
        │                        tests: keys, relationships, censoring interval
        ├──────────────► looker/        LookML model + explore, access_filter on huc8
        │                               validated offline against the built schema
        ├──────────────► embed/         Metabase OSS + FastAPI host minting signed,
        │                               tenant-locked embed URLs
        └──────────────► hex/           planned app; SQL contract and setup notes
```

## Quickstart

```sh
make setup     # uv venv with dbt-duckdb, lkml, fastapi
make build     # builds DuckDB warehouse and runs 15 dbt tests, under a second
make test      # plus offline LookML validation and embed-token tests
```

`make test` is what CI runs. Nothing above needs Docker or an account.

For the embedded dashboard (Docker) see [embed/README.md](embed/README.md).
For the Hex app (free Hex account plus a hosted Postgres or MotherDuck) see
[hex/README.md](hex/README.md).

## What is in here

| Path | What |
| --- | --- |
| `warehouse/` | dbt project. Source is the CSV read in place by dbt-duckdb. Marts carry Lightdash-style `meta` metric definitions. |
| `looker/` | LookML model, three views, one explore. No live Looker behind it; `tests/test_lookml.py` keeps it honest. |
| `embed/` | docker-compose for Postgres + Metabase, and a FastAPI host that authenticates demo users, authorizes tenants and mints signed embed URLs. |
| `hex/` | Planned app, build notes and a censoring-safe SQL contract; no published link/export yet. |
| `scripts/` | Copies marts from DuckDB into any Postgres so hosted tools can read them. |
| `docs/` | The deployment opinion and three ADRs. |
| `data/seed/` | The snapshot and its provenance. |

## The data

USGS groundwater results for San Bernardino County, California, 2000 to
2023: arsenic and two nitrate definitions, about 7,700 results across about
1,000 wells. It is the cleaned output of the companion
[groundwater-audit](../groundwater-audit) project. Non-detects are kept as
censored intervals rather than substituted, and the marts expose that so a
dashboard cannot accidentally report a detection limit as a measurement.

## What this does and does not demonstrate

Hex's git export, a live Looker instance, and interactive embedding are all
paid features. The repository shows what the free tiers allow and says
exactly where the line is in [docs/adr/0003](docs/adr/0003-what-the-free-tiers-do-not-show.md).

## Metric and authorization contract

`detected_value` is null for non-detects and DNQ. Detected measurements do not
need a reporting limit and remain included even if the limit is absent. Default
concentration aggregates use this field and are labelled **detected subset**;
they are not population medians or evidence of a trend. Raw `value` remains
available for audit but hidden in default semantic dimensions. Counts and
non-detect shares include all result rows, separated by constituent definition.

The host rejects unauthenticated requests and unauthorized tenant selections.
A server-side demo identity registry defines entitlements; URL slugs never grant
access. See [embed/README.md](embed/README.md) for session setup and limitations.
