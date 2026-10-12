# Embedded analytics demo

A tenant-scoped dashboard embedded in a host app, using Metabase open source
and signed JWTs. The host authentication demo is testable without a browser or BI account. Docker/Metabase setup is optional.

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
   non-detects per year, median detected concentration (detected subset) by constituent.
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

## Demo authentication

The host denies anonymous requests by default. Set independent secrets for
Metabase and host sessions, and configure demo identities server-side:

```sh
export DEMO_USERS_JSON='{"alice":{"token":"replace-with-random-demo-token","tenants":["santa-ana"]}}'
export DEMO_SESSION_SECRET='replace-with-an-independent-random-session-secret'
# Only for HTTP localhost testing; HTTPS uses secure cookies by default.
export DEMO_COOKIE_SECURE=false
curl -c /tmp/groundwater-demo.cookies -X POST http://localhost:8000/session \
  -H 'Authorization: Bearer replace-with-random-demo-token'
curl -b /tmp/groundwater-demo.cookies http://localhost:8000/token/santa-ana
# /token/mojave is 403 for alice, even with a valid host session.
```

The JSON token endpoint also accepts bearer credentials directly. The HttpOnly,
SameSite host cookie expires in 15 minutes. It never accepts a client-supplied
list of tenants; every request rechecks the identity registry. Replace this demo
registry with your application's identity provider before production use.

## What it demonstrates

- The host app owns identity and authorization. The BI tool only sees a
  signed token with locked parameters.
- Tokens are short-lived and minted per page load, so revoking access is a
  config change in the host app, not a BI-tool permission edit.
- The watershed registry lives in `embed/app/main.py`; the server-side
  `DEMO_USERS_JSON` grants each identity only its allowed tenant slugs.
  Production identity must come from the host application's login provider.
- A previously minted Metabase URL remains usable until its short expiry;
  revocation prevents new URLs, not immediate invalidation of existing ones.

## What it does not demonstrate

Static embedding gives read-only dashboards with no drill-through and no
per-viewer session. Interactive embedding, where each viewer gets a sandboxed
session and can explore, is a paid tier in Metabase, and the Looker
equivalent (SSO embed with user attributes) needs a Looker instance. The
LookML in `looker/` shows how the same scoping would be expressed there via
`access_filter`.
