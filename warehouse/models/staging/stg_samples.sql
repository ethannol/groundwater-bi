-- One row per laboratory result. Casts are explicit so downstream models do
-- not depend on DuckDB CSV type inference.
with src as (
    select * from {{ source('wqp', 'wqp_samples') }}
)

select
    result_id,
    site_id,
    activity_id,
    activity_type,
    cast("date" as date)                              as sample_date,
    characteristic,
    family,
    fraction,
    nullif(method_id, '')                             as method_id,
    nullif(method_name, '')                           as method_name,
    cast(value as double)                             as value,
    unit,
    cast(lower as double)                             as lower_bound,
    cast(upper as double)                             as upper_bound,
    cast(censored as boolean)                         as is_censored,
    cast(dnq as boolean)                              as is_dnq,
    cast(estimated as boolean)                        as is_estimated,
    cast(dl as double)                                as detection_limit,
    cast(dl_missing as boolean)                       as is_dl_missing,
    site_name,
    site_type,
    lpad(cast(huc8 as varchar), 8, '0')               as huc8,
    cast(lat as double)                               as latitude,
    cast(lon as double)                               as longitude,
    nullif(aquifer, '')                               as aquifer,
    nullif(aquifer_type, '')                          as aquifer_type,
    cast(well_depth_ft as double)                      as well_depth_ft
from src
