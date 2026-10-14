# TxDOT Roadway Inventory — source record for the §7 ground-truth spot-check

External public data, used only in WRITEUP §7 (Best Bias Discovery). Never read by the scored submission. It is TxDOT's own
roadway inventory, not a TIGER/Line derivative and not one of the four reference layers removed from the challenge on
2026-09-25.

## Service

- Dataset: **TxDOT Roadway Inventory** (statewide; every public road in Texas — state-, county- and city-maintained,
  on- and off-system — dynamically segmented by attribute; published annually from end-of-year HPMS reporting).
- Feature service layer queried: `https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_Roadway_Inventory/FeatureServer/0`
  (query endpoint `.../FeatureServer/0/query`; public, no sign-up, no key).
- ArcGIS Online item (metadata and licence): `https://www.arcgis.com/home/item.html?id=843ebe994c114961a855ec76ddcde086`
  (`serviceItemId` of the service; owner `TPP_GIS`; "Last Revision: 08/27/2025" in the service description).
- Listed on the TxDOT Open Data Portal: `https://gis-txdot.opendata.arcgis.com/` and on `https://www.txdot.gov/data-maps/roadway-inventory.html`.
- Retrieval date: **2026-10-14 UTC** (evening of 2026-10-13 local time; UTC timestamps per response in each frozen file and in `txdot_responses/_service/retrieved.txt`).
- Frozen copies of the layer and item metadata as served that day: `txdot_responses/_service/layer.json`, `txdot_responses/_service/item.json`.

## Query (identical for every segment)

```
GET {layer}/query?f=json&geometry={lon},{lat}&geometryType=esriGeometryPoint&inSR=4326
    &spatialRel=esriSpatialRelIntersects&distance=30&units=esriSRUnit_Meter
    &outFields=STE_NAM,HWY,HSYS,RDWAY_MAINT_AGCY,F_SYSTEM,RU,ADT_CUR,SRF_TYPE&returnGeometry=false
```

`{lon},{lat}` is the middle vertex of the Overture segment (OGC:CRS84, rounded to 6 decimals). A segment is "in the
inventory" when the response has ≥ 1 feature within 30 m; it "has a TxDOT name" when any returned `STE_NAM` (street
name) or `HWY` (highway id) is non-empty. Requests were spaced ≥ 0.5 s apart (≤ 2 per second), `User-Agent`
`zindi-bias-bounty-spotcheck/1.0`.

## Sample (deterministic, challenge data only)

Per county (Maverick 48323, Zapata 48505, Brooks 48047, Kinney 48271, Zavala 48507, Edwards 48137): drivable segments
of `south-central-tx-overture-roads.parquet` (the scored layer) with LINESTRING geometry lying within the union of the
county's scored tracts, ordered by `md5(id)`; the first 30 with `names.primary` null (unnamed) and the first 30 with a
name (control). Overture lengths (`ST_Length_Spheroid`) are kept for the km-weighted summary. No random number
generator is involved; re-running `spotcheck_txdot.py` without `--offline` draws the same 360 segments.

## Frozen responses and verification

- `txdot_responses/<county>/<overture segment id>.json` — one file per query: the segment's Overture attributes, the
  exact URL and parameters, the UTC retrieval time, the SHA-256 of the raw response bytes and the raw response text
  verbatim (`response_raw`). Responses contain only the eight requested attribute fields, no geometry.
- `txdot_responses/SHA256SUMS` — GNU-format manifest of every frozen file (`sha256sum -c SHA256SUMS` inside that folder,
  or `python spotcheck_txdot.py --offline`, which verifies the manifest and rebuilds `spotcheck_txdot_results.csv` and
  `spotcheck_txdot_summary.md` from the frozen files alone — no network, no challenge data).

## Licence / terms (as retrieved 2026-10-13 local, 2026-10-14 UTC)

The ArcGIS Online item's `licenseInfo` field (frozen in `txdot_responses/_service/item.json`) reads, verbatim:

> Copyright Texas Department of Transportation. This data was produced for internal use and is provided for
> informational purposes only, and is subject to change. TxDOT makes no warranty of any kind as to the accuracy or
> validity of the data provided. GIS content and data provided is the property of TxDOT and may not be used for
> commercial purposes or resold. Distribution of this content to third parties without TxDOT's written consent is
> strictly prohibited.

The portal's terms page `https://gis-txdot.opendata.arcgis.com/pages/terms-of-use` was retrieved the same day (HTTP 200)
but the served HTML is a JavaScript application shell with no licence text in it; no separate licence statement was
found there, so the item `licenseInfo` above is the operative statement we can cite. The frozen responses are kept
solely so that the finding can be verified without re-querying; they are a non-commercial excerpt of eight attribute
fields for 360 point queries. If TxDOT objects to their presence in the repository they will be removed, and the check
remains reproducible online with `python spotcheck_txdot.py` (same deterministic sample, same query).

Service attribution (service `copyrightText`): "TxDOT - Transportation Planning and Programming Division (TPP) | Data
Management - TPP-GIS@txdot.gov".
