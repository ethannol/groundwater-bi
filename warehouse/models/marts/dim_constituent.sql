-- One row per comparable measurement definition. Family alone is not enough:
-- the same family can arrive under different characteristic names, fractions
-- and units, and those are not interchangeable without justification.
select distinct
    concat_ws('|', family, characteristic, fraction, unit) as constituent_key,
    family,
    characteristic,
    fraction,
    unit
from {{ ref('stg_samples') }}
