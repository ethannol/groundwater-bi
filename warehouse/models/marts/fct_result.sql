-- Grain: one laboratory result (result_id). Censored results keep their
-- interval bounds so a consumer can choose how to treat non-detects instead
-- of inheriting a silent substitution.
select
    result_id,
    site_id                                                         as well_key,
    concat_ws('|', family, characteristic, fraction, unit)         as constituent_key,
    activity_id,
    activity_type,
    sample_date,
    cast(extract(year from sample_date) as integer)                as sample_year,
    method_id,
    value,
    lower_bound,
    upper_bound,
    detection_limit,
    is_censored,
    is_dnq,
    is_estimated,
    is_dl_missing,
    cast(is_censored as integer)                                    as censored_flag,
    cast(is_dl_missing as integer)                                  as dl_missing_flag
from {{ ref('stg_samples') }}
