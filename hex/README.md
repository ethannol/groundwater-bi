# Hex app

**Status: planned.** No Hex notebook export or published app exists yet.
The repository supplies a runnable SQL contract in [metrics.sql](metrics.sql)
and build notes for a future app. Account provisioning, notebook creation and
publication remain manual work; this is not a third validated consumer.

## Setup (Hex Community plan)

Hex needs a database it can reach over the network. Two free options:

1. **Neon Postgres.** Create a project, copy the connection string, then
   `PG_URL='postgresql://...?sslmode=require' make export-pg`.
2. **MotherDuck.** Upload `warehouse/target/groundwater.duckdb` or attach it;
   Hex has a native MotherDuck connection.

Then in Hex: add the data connection, create a project, and build cells in
this order:

1. SQL: result counts, wells sampled and share non-detect by `sample_year`
   and `family`, from `fct_result` joined to `dim_constituent`.
2. SQL: the consistent cohort. Wells with a result in both the first and
   last three years of the record, for the selected family.
3. Start with the result/well counts, non-detect share and explicitly labelled
   detected-subset median from `metrics.sql`. Never use `median(value)`:
   non-detect values are reporting limits. A pooled/cohort concentration chart
   requires a separate censoring-aware estimator and fixed well/period rules;
   the SQL subset median alone cannot support it.
4. An input parameter for `family` wired into the SQL cells, so the
   published app has one control.
5. A short markdown cell stating what the comparison does and does not
   support (descriptive change in observed concentrations; not remediation
   effect, not aquifer-wide trend).

Publish the app, then:

- paste the public app link below;
- export the project as `.ipynb` into this folder;
- add one or two screenshots to `hex/screenshots/`.

Git export of the project YAML is a Team/Enterprise feature and is not
included; see `docs/adr/0003`.

## Published app

_Link pending._
