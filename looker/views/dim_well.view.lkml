view: dim_well {
  sql_table_name: main.dim_well ;;

  dimension: well_key {
    primary_key: yes
    type: string
    sql: ${TABLE}.well_key ;;
  }

  dimension: well_name {
    type: string
    sql: ${TABLE}.well_name ;;
  }

  dimension: huc8 {
    type: string
    label: "HUC-8 watershed"
    sql: ${TABLE}.huc8 ;;
  }

  dimension: aquifer {
    type: string
    sql: ${TABLE}.aquifer ;;
  }

  dimension: aquifer_type {
    type: string
    sql: ${TABLE}.aquifer_type ;;
  }

  dimension: well_depth_ft {
    type: number
    sql: ${TABLE}.well_depth_ft ;;
  }

  dimension: location {
    type: location
    sql_latitude: ${TABLE}.latitude ;;
    sql_longitude: ${TABLE}.longitude ;;
  }

  measure: n_wells {
    type: count
    label: "Wells"
  }
}
