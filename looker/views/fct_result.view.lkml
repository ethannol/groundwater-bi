view: fct_result {
  sql_table_name: main.fct_result ;;

  dimension: result_id {
    primary_key: yes
    type: string
    sql: ${TABLE}.result_id ;;
  }

  dimension: well_key {
    type: string
    hidden: yes
    sql: ${TABLE}.well_key ;;
  }

  dimension: constituent_key {
    type: string
    hidden: yes
    sql: ${TABLE}.constituent_key ;;
  }

  dimension: activity_type {
    type: string
    sql: ${TABLE}.activity_type ;;
  }

  dimension_group: sample {
    type: time
    timeframes: [date, month, year]
    datatype: date
    sql: ${TABLE}.sample_date ;;
  }

  dimension: sample_year {
    type: number
    sql: ${TABLE}.sample_year ;;
  }

  dimension: method_id {
    type: string
    sql: ${TABLE}.method_id ;;
  }

  dimension: value {
    hidden: yes
    type: number
    description: "Reported value. For censored rows this is the detection limit, not a measurement."
    sql: ${TABLE}.value ;;
  }

  dimension: lower_bound {
    type: number
    sql: ${TABLE}.lower_bound ;;
  }

  dimension: upper_bound {
    type: number
    sql: ${TABLE}.upper_bound ;;
  }

  dimension: detection_limit {
    type: number
    sql: ${TABLE}.detection_limit ;;
  }

  dimension: is_censored {
    type: yesno
    sql: ${TABLE}.is_censored ;;
  }

  dimension: is_dl_missing {
    type: yesno
    sql: ${TABLE}.is_dl_missing ;;
  }

  measure: n_results {
    type: count
    label: "Results"
  }

  measure: n_wells {
    type: count_distinct
    label: "Wells sampled"
    sql: ${well_key} ;;
  }

  dimension: detected_value {
    type: number
    description: "Measured detections only, excluding ND and DNQ. Detected results need no reporting limit. Not a censored-population estimate."
    sql: ${TABLE}.detected_value ;;
  }

  measure: median_detected_value {
    type: median
    label: "Median detected concentration (detected subset)"
    sql: ${detected_value} ;;
    value_format_name: decimal_2
  }

  measure: n_censored {
    type: sum
    label: "Non-detects"
    sql: ${TABLE}.censored_flag ;;
  }

  measure: pct_censored {
    type: number
    label: "Share non-detect"
    sql: 1.0 * ${n_censored} / nullif(${n_results}, 0) ;;
    value_format_name: percent_1
  }

  measure: n_dl_missing {
    type: sum
    label: "Results missing a detection limit"
    sql: ${TABLE}.dl_missing_flag ;;
  }
}
