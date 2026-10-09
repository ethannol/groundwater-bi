# Embedded analytics demo

A tenant-scoped dashboard embedded in a host app, using Metabase open source
and signed JWTs. Everything here runs locally and costs nothing.

## Run it

```sh
make build            # DuckDB marts
make embed-up         # Postgres + Metabase in Docker
make export-pg        # copy dim_well, dim_constituent, fct_result into Postgres
```

Then in Metabase (http://localhost:3000):

1. Finish the setup wizard. Add a Postgres database: host `warehouse`, port
   `5432`, db/user/password `groundwater`.
2. Build a dashboard from `fct_result` joined to `dim_well` and
   `dim_constituent`. A sensible first one: wells sampled per year, share of
   non-detects per year, median reported value by constituent.
3. Add a dashboard filter on `dim_well.huc8`.
4. Admin settings, Embedding, enable static embedding and copy the secret key.
5. On the dashboard, Sharing, Embed, set the `huc8` parameter to **Locked**,
   publish, and note the dashboard id in the URL.

Then:

```sh
cp embed/.env.example embed/.env   # fill in the secret and dashboard id
set -a; source embed/.env; set +a
make serve-embed                   # http://localhost:8000
```

## What it demonstrates

- The host app owns identity and authorization. The BI tool only sees a
  signed token with locked parameters.
- Tokens are short-lived and minted per page load, so revoking access is a
  config change in the host app, not a BI-tool permission edit.
- The tenant-to-watershed mapping lives in `embed/app/main.py` for the demo.
  In production it comes from the session.

## What it does not demonstrate

Static embedding gives read-only dashboards with no drill-through and no
per-viewer session. Interactive embedding, where each viewer gets a sandboxed
session and can explore, is a paid tier in Metabase, and the Looker
equivalent (SSO embed with user attributes) needs a Looker instance. The
LookML in `looker/` shows how the same scoping would be expressed there via
`access_filter`.
