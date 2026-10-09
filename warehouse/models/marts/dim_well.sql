-- One row per monitoring well. Station metadata is repeated on every result
-- row in the source; keep the most recently sampled version if it varies.
with ranked as (
    select
        site_id                                   as well_key,
        site_name                                 as well_name,
        site_type,
        huc8,
        latitude,
        longitude,
        aquifer,
        aquifer_type,
        well_depth_ft,
        row_number() over (
            partition by site_id order by sample_date desc, result_id
        )                                         as rn
    from {{ ref('stg_samples') }}
)

select
    well_key,
    well_name,
    site_type,
    huc8,
    latitude,
    longitude,
    aquifer,
    aquifer_type,
    well_depth_ft
from ranked
where rn = 1
