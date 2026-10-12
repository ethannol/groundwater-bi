# ADR 0003: What this repository demonstrates versus describes

**Status:** accepted · 2026-10-07

## Context

The three tools in scope have different free-tier boundaries, and a portfolio
repository should not imply it exercised features it could not.

## Decision

| Tool | Shown here | Described only | Why |
| --- | --- | --- | --- |
| Hex | A planned app, setup notes and a tested SQL metric contract in `hex/`; no notebook export or published app exists yet | App creation/publication and git export / git sync | App work remains manual; git integration was outside the exercised scope |
| Looker | LookML model, views, explore with `access_filter`; offline structural validation in CI | Live instance, Looker validator, Spectacles SQL validation, SSO embed | No free plan; trial is sales-assisted |
| Embedded | Metabase OSS static embed with signed, locked-parameter JWTs | Interactive embedding with per-viewer sandboxes | Paid tier in Metabase; embedding is enterprise-only in self-hosted Lightdash |

## Consequences

- Readers can tell at a glance which claims are backed by running code.
- If a Looker instance or a Hex Team workspace becomes available, the
  "described only" column has a concrete list of what to add: Spectacles in
  CI, the exported Hex YAML in `hex/`, and an SSO-embed variant of the host
  app.
