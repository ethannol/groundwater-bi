# Data source

`wqp_samples.csv` is a column subset of `data/processed/analysis_samples.csv`
from the companion [groundwater-audit](../../../groundwater-audit) project,
which retrieved it from the Water Quality Portal on 2026-10-07 and applied the
cleaning and exclusion steps documented there.

- Source: Water Quality Portal (https://www.waterqualitydata.us), legacy WQX
  2.x `resultPhysChem` profile.
- Query: California (US:06), San Bernardino County (US:06:071), site type
  Well, characteristics Arsenic, Nitrate, Inorganic nitrogen (nitrate and
  nitrite), start date 2000-01-01.
- All rows are USGS NWIS records (organization USGS-CA), which are public
  domain U.S. Government works. Suggested citation: National Water Quality
  Monitoring Council, Water Quality Portal, accessed 2026-10-07,
  https://www.waterqualitydata.us.
- Rows: 7,733 results across 1,012 wells, 2000-03 to 2023-05.
- Censoring is preserved: `censored`, `lower`, `upper`, `dl`, `dl_missing`.
  Non-detects have **not** been replaced by zero, the limit, or half the
  limit. `value` for a censored row is the reporting limit.
- `huc8` is an eight-digit code and is stored zero-padded as text downstream.

The snapshot is intentionally small so the whole stack builds in seconds. The
snapshot itself is never edited; every transformation lives in `warehouse/`.
