# ADR 0002: Embedded viewers are scoped by a signed token, not by UI filters

**Status:** accepted · 2026-10-07

## Context

The embed demo serves dashboards to several "tenants", each allowed to see
one HUC-8 watershed. The scoping must hold even if a viewer edits the iframe
URL or the dashboard filters.

## Decision

- The host app (`embed/app/main.py`) maps the authenticated tenant to a
  watershed and mints a short-lived HS256 JWT whose `params` lock `huc8`.
- Metabase static embedding is used because it is free. The same pattern
  applies to Looker SSO embedding, where the signed URL carries user
  attributes and the explore's `access_filter` enforces them; that filter is
  declared in `looker/models/groundwater.model.lkml`.
- Tokens expire in minutes and are minted per page load.

## Consequences

- Revoking a tenant's access is a change in the host app, with no BI-tool
  permission edit.
- Static embeds are read-only with no drill-through and no per-viewer
  session. Interactive embedding (paid in Metabase) would be required for
  self-serve exploration inside the product.
- The tenant registry is a dict in the demo; in production it comes from
  the session store.
