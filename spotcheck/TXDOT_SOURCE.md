# TxDOT Roadway Inventory — source record for the §7 ground-truth spot-check

External public data, used only in WRITEUP §7 (Best Bias Discovery). Never read by the scored submission. It is TxDOT's own
roadway inventory, not a TIGER/Line derivative and not one of the four reference layers removed from the challenge on
2026-09-25.

## Service

- Dataset: **TxDOT Roadway Inventory** (statewide; every public road in Texas — state-, county- and city-maintained,
  on- and off-system — dynamically segmented by attribute; published annually from end-of-year HPMS reporting).
- Feature service layer queried: `https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_Roadway_Inventory/FeatureServer/0`
  (query endpoint `.../FeatureServer/0/query`; publicly accessible without sign-up or key).
- ArcGIS Online item (metadata and licence): `https://www.arcgis.com/home/item.html?id=843ebe994c114961a855ec76ddcde086`
  (`serviceItemId` of the service; owner `TPP_GIS`; "Last Revision: 08/27/2025" in the service description).
- Listed on the TxDOT Open Data Portal: `https://gis-txdot.opendata.arcgis.com/` and on `https://www.txdot.gov/data-maps/roadway-inventory.html`.
- Retrieval date: **2026-10-14 UTC** (evening of 2026-10-13 local time; the UTC timestamp of every query is in
  `spotcheck_txdot_results.csv`, column `retrieved_utc`).

## Query (identical for every segment)

```
GET {layer}/query?f=json&geometry={lon},{lat}&geometryType=esriGeometryPoint&inSR=4326
    &spatialRel=esriSpatialRelIntersects&distance=30&units=esriSRUnit_Meter
    &outFields=STE_NAM,HWY,HSYS,RDWAY_MAINT_AGCY,F_SYSTEM,RU,ADT_CUR,SRF_TYPE&returnGeometry=false
```

`{lon},{lat}` is the middle vertex of the Overture segment (OGC:CRS84, rounded to 6 decimals; both are in the results
table). A segment is "in the inventory" when the response has ≥ 1 feature within 30 m; it "has a TxDOT name" when any
returned `STE_NAM` (street name) or `HWY` (highway id) is non-empty. Requests were spaced ≥ 0.5 s apart (≤ 2 per
second), `User-Agent` `zindi-bias-bounty-spotcheck/1.0`.

## Sample (deterministic, challenge data only)

Per county (Maverick 48323, Zapata 48505, Brooks 48047, Kinney 48271, Zavala 48507, Edwards 48137): drivable segments
of `south-central-tx-overture-roads.parquet` (the scored layer) with LINESTRING geometry lying within the union of the
county's scored tracts, ordered by `md5(id)`; the first 30 with `names.primary` null (unnamed) and the first 30 with a
name (control). Overture lengths (`ST_Length_Spheroid`) are kept for the km-weighted summary. No random number
generator is involved; re-running `spotcheck_txdot.py` draws the same 360 segments.

## Licence / terms (as retrieved 2026-10-13 local, 2026-10-14 UTC) and what is published

The ArcGIS Online item's `licenseInfo` field reads, verbatim:

> Copyright Texas Department of Transportation. This data was produced for internal use and is provided for
> informational purposes only, and is subject to change. TxDOT makes no warranty of any kind as to the accuracy or
> validity of the data provided. GIS content and data provided is the property of TxDOT and may not be used for
> commercial purposes or resold. Distribution of this content to third parties without TxDOT's written consent is
> strictly prohibited.

The portal's terms page `https://gis-txdot.opendata.arcgis.com/pages/terms-of-use` was retrieved the same day (HTTP
200) but the served HTML is a JavaScript application shell with no licence text in it; no separate licence statement
was found there, so the item `licenseInfo` above is the operative statement. The inventory is publicly accessible
without sign-up, but this licence restricts redistribution of its content. **The raw responses are therefore not
redistributed.** They are retained locally by the author (outside the repository) in case the organisers ask to see
them. What the repository publishes is our own work:

- `spotcheck_txdot_results.csv` — one row per queried segment: Overture segment id, county, sample (unnamed / named
  control), class, import-era flag and last Overture update, Overture length and midpoint, the number of inventory
  features returned, `in_inventory`, `has_txdot_name`, the UTC retrieval time and the SHA-256 of the raw response bytes.
  No TxDOT attribute values (names, highway ids, maintenance agency, …) are included.
- `SHA256SUMS` — the SHA-256 of every raw response file (360 queries plus the service layer and item metadata as served),
  kept as a tamper-evidence record of what was seen on 2026-10-14 UTC.
- `spotcheck_txdot_summary.md` — the six-county table, rebuilt from the results CSV by
  `python spotcheck_txdot.py --offline` (no network, no challenge data).

Reproduction is online: `PYTHONUTF8=1 python spotcheck_txdot.py` (needs the challenge data folder) re-draws the same
360 segments and re-queries the service with the parameters above; the inventory is revised annually, so a later run
may differ for individual segments.

Service attribution (service `copyrightText`): "TxDOT - Transportation Planning and Programming Division (TPP) | Data
Management - TPP-GIS@txdot.gov".
