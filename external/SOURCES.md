# External public data used in WRITEUP §7 only

Nothing in this folder, and nothing fetched by `spotcheck_txdot.py`, is used by the scored submission. None of it is a
copy of the four reference layers removed on 2026-09-25 (TIGER/Line roads, Microsoft building footprints, HIFLD
facilities, CBP establishments).

## 1. County names (labels only)

- File: `census_gaz_counties_2023_subset.csv` — columns `USPS, STATEFP, COUNTYFP, NAME`; the 476 counties of AZ, CA,
  NM, OK, TX, WA extracted from the US Census Bureau 2023 Gazetteer county file.
- Source: `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip`
  (US Census Bureau, public domain). Retrieved 2026-10-13.
- SHA-256 of the downloaded zip: `919df59ba90759cce85468c0337e898e4b39c08eaffce86ddd88fa41f1f7f0c8`;
  of the extracted `2023_Gaz_counties_national.txt`: `b0aecde6748947236e931faeb6a619b89aea0346e54a454239aac76abcd2ef82`;
  of the subset CSV: `3437a3e4612310e6c42cbe00050a2474d3031cfc3d9240dde6773ec655ea9eff`.
- Use: `bias_discovery.py` maps `STATEFP + COUNTYFP` (both provided in the challenge strata table) to a county name
  for the tract tables. No number depends on it; without the file the FIPS code is printed instead.

## 2. TxDOT Roadway Inventory (ground-truth spot-check)

See `../spotcheck/TXDOT_SOURCE.md` for the feature-service URL, the exact query parameters, the retrieval date, the
licence statement, what is published (our per-segment observations and the SHA-256 of each response; raw responses are not redistributed) and the online reproduction command.
