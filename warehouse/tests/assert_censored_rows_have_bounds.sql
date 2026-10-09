-- A censored result must carry an interval. If this returns rows, the
-- upstream censoring logic broke and every downstream metric is suspect.
select result_id
from {{ ref('fct_result') }}
where is_censored
  and (lower_bound is null or upper_bound is null)
