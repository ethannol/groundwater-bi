-- Planned Hex consumer: run over the built/exported marts.
-- Never aggregate raw value: a non-detect's value is its reporting limit.
-- detected_subset_median is not a population/censoring-aware median.
select c.family, c.characteristic, c.fraction, c.unit, r.sample_year,
       count(*) as n_results,
       count(distinct r.well_key) as n_wells,
       sum(r.censored_flag) as n_censored,
       1.0 * sum(r.censored_flag) / nullif(count(*), 0) as pct_censored,
       median(r.detected_value) as median_detected_value
from fct_result r
join dim_constituent c on c.constituent_key = r.constituent_key
group by c.family, c.characteristic, c.fraction, c.unit, r.sample_year
order by c.family, c.characteristic, c.fraction, c.unit, r.sample_year
