view: dim_constituent {
  sql_table_name: main.dim_constituent ;;

  dimension: constituent_key {
    primary_key: yes
    type: string
    hidden: yes
    sql: ${TABLE}.constituent_key ;;
  }

  dimension: family {
    type: string
    sql: ${TABLE}.family ;;
  }

  dimension: characteristic {
    type: string
    sql: ${TABLE}.characteristic ;;
  }

  dimension: fraction {
    type: string
    sql: ${TABLE}.fraction ;;
  }

  dimension: unit {
    type: string
    sql: ${TABLE}.unit ;;
  }
}
