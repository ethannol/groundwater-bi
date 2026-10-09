# ADR 0001: Metric definitions live in git and are validated in CI

**Status:** accepted · 2026-10-07

## Context

Metrics defined in a BI tool's UI are invisible to code review and drift
from the warehouse. The team needs a single definition for "wells sampled",
"non-detect share" and similar measures across notebooks, explores and
embedded dashboards.

## Decision

- dbt marts carry metric and dimension metadata in `schema.yml` `meta`
  blocks, following the Lightdash convention so a Lightdash explore could
  be generated from them without changes.
- A LookML model in `looker/` mirrors those definitions for a Looker
  deployment.
- CI builds the warehouse, then runs `tests/test_lookml.py`, which parses the
  LookML and checks every table and column reference against the built
  DuckDB schema, and every join field against the view definitions.

## Consequences

- A renamed column fails the pull request.
- Two copies of the definitions (dbt meta and LookML) must be kept in sync.
  A follow-up could generate the LookML from the dbt manifest.
- Without a Looker instance the check is structural, not semantic; see
  ADR 0003.
