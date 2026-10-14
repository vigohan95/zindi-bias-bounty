TxDOT Roadway Inventory within 30 m of the segment midpoint; 6 counties (brooks, edwards, kinney, maverick, zapata, zavala); retrieved 2026-10-14 to 2026-10-14 UTC. Derived from our per-segment observation table (`spotcheck_txdot_results.csv`); raw responses are not redistributed (see TXDOT_SOURCE.md).

Pooled: unnamed 163/180 absent from the inventory (89.5% of sampled unnamed km), 17/180 carry a TxDOT name or highway id; named controls 161/180 in the inventory, 161/180 with a TxDOT name or highway id.

| county   | sample          |   n |   in_inventory |   with_txdot_name |   absent |   sampled_km |   absent_km_share |   median_len_m | classes                                                                        |
|:---------|:----------------|----:|---------------:|------------------:|---------:|-------------:|------------------:|---------------:|:-------------------------------------------------------------------------------|
| brooks   | named (control) |  30 |             28 |                28 |        2 |         12.1 |             0.164 |            136 | residential 22, tertiary 5, unclassified 2, primary 1                          |
| brooks   | unnamed         |  30 |              2 |                 2 |       28 |         33.1 |             0.975 |            806 | residential 28, motorway 1, secondary 1                                        |
| edwards  | named (control) |  30 |             24 |                24 |        6 |         13.1 |             0.247 |            291 | residential 25, trunk 2, primary 2, tertiary 1                                 |
| edwards  | unnamed         |  30 |              4 |                 4 |       26 |         22.7 |             0.596 |            390 | residential 28, secondary 2                                                    |
| kinney   | named (control) |  30 |             22 |                22 |        8 |         12.4 |             0.214 |            134 | residential 22, secondary 5, trunk 2, tertiary 1                               |
| kinney   | unnamed         |  30 |              2 |                 2 |       28 |         25.5 |             0.913 |            575 | residential 28, trunk 1, tertiary 1                                            |
| maverick | named (control) |  30 |             29 |                29 |        1 |          5.2 |             0.197 |            117 | residential 26, tertiary 1, primary 1, trunk 1, secondary 1                    |
| maverick | unnamed         |  30 |              2 |                 2 |       28 |         24.3 |             0.994 |            729 | residential 28, unclassified 1, trunk 1                                        |
| zapata   | named (control) |  30 |             29 |                29 |        1 |          6.9 |             0.008 |            111 | residential 19, tertiary 5, trunk 4, primary 2                                 |
| zapata   | unnamed         |  30 |              3 |                 3 |       27 |         34.7 |             0.941 |            770 | residential 25, unclassified 5                                                 |
| zavala   | named (control) |  30 |             29 |                29 |        1 |         10.8 |             0.107 |            141 | residential 25, trunk 4, secondary 1                                           |
| zavala   | unnamed         |  30 |              4 |                 4 |       26 |         33.2 |             0.887 |            795 | residential 29, secondary 1                                                    |
| POOLED   | named (control) | 180 |            161 |               161 |       19 |         60.5 |             0.167 |            133 | residential 139, tertiary 13, trunk 13, secondary 7, primary 6, unclassified 2 |
| POOLED   | unnamed         | 180 |             17 |                17 |      163 |        173.5 |             0.895 |            697 | residential 166, unclassified 6, secondary 4, trunk 2, motorway 1, tertiary 1  |

Unnamed sample split by Overture edit age (import_era = latest `sources[].update_time` before 2012-01-01):

| import_era   |   n |   absent |    km |
|:-------------|----:|---------:|------:|
| False        |  64 |       53 |  70.5 |
| True         | 116 |      110 | 103.1 |
