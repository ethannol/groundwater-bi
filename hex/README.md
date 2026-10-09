# Hex app

The Hex side of the stack: a notebook that reads the marts, walks through the
cohort-versus-pooled comparison and the censoring profile, and is published
as an app with a constituent selector.

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
3. Python: pooled median by year versus cohort median by year, on one chart,
   with the non-detect share underneath. The difference between the two
   lines is the sampling-composition effect the audit project describes.
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
