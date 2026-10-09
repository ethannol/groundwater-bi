# LookML model for the groundwater warehouse.
#
# There is no live Looker instance behind this repository (Looker has no free
# tier). The files are kept honest by tests/test_lookml.py, which parses them
# and checks every ${TABLE}.column reference against the built DuckDB schema.

connection: "groundwater_duckdb"

include: "/views/*.view.lkml"

explore: fct_result {
  label: "Groundwater results"
  description: "One row per laboratory result, joined to well and constituent."

  join: dim_well {
    type: left_outer
    relationship: many_to_one
    sql_on: ${fct_result.well_key} = ${dim_well.well_key} ;;
  }

  join: dim_constituent {
    type: left_outer
    relationship: many_to_one
    sql_on: ${fct_result.constituent_key} = ${dim_constituent.constituent_key} ;;
  }

  # Row-level scoping for embedded viewers: the embed token carries a
  # huc8 user attribute and the explore filters on it. See docs/adr/0002.
  access_filter: {
    field: dim_well.huc8
    user_attribute: huc8
  }
}
