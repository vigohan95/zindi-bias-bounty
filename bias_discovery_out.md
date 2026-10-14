# bias_discovery.py output — Overture 2026-08-19.0 scored road layer, five regions; import-age cutoff 2012-01-01
extracted 140642 rows -> <data>/features/road_attrs.parquet

## 1. Unnamed drivable road km share (km-weighted), all five regions
tracts with road km: 9,792; road km: 1,069,751; unnamed km: 263,772
overall unnamed share: 0.247  (minor classes only: 0.229; residential only: 0.247)
unnamed AND unedited since 2011 ('import-era' km): 78,984 km = 0.074 of all road km, 0.299 of unnamed km

## 2. Edit age (latest `sources[].update_time` < 2012-01-01) by region and by scorecard stratum
Columns: n tracts; road km; unnamed km; share of UNNAMED km unedited since 2011; share of NAMED km unedited since 2011; unnamed-and-unedited km; that km as a share of all road km; median tract unnamed-and-unedited share.

### edit age by region
| region           |   tracts |   road_km |   unnamed_km |   unnamed_share |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_km |   unnamed_stale_share |   median_tract_unnamed_stale_share |
|:-----------------|---------:|----------:|-------------:|----------------:|-------------------------:|-----------------------:|-------------------:|----------------------:|-----------------------------------:|
| eastern-ok       |     1192 |    213301 |        69510 |           0.326 |                    0.187 |                  0.088 |              12985 |                 0.061 |                                  0 |
| eastern-wa       |      415 |     79164 |         6968 |           0.088 |                    0.078 |                  0.006 |                545 |                 0.007 |                                  0 |
| maricopa-az      |     1593 |    123557 |        14898 |           0.121 |                    0.083 |                  0.005 |               1236 |                 0.01  |                                  0 |
| northern-ca      |      591 |     77431 |        14508 |           0.187 |                    0.355 |                  0.047 |               5149 |                 0.066 |                                  0 |
| south-central-tx |     6001 |    576297 |       157888 |           0.274 |                    0.374 |                  0.058 |              59070 |                 0.102 |                                  0 |

### edit age by ur_class
| ur_class   |   tracts |   road_km |   unnamed_km |   unnamed_share |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_km |   unnamed_stale_share |   median_tract_unnamed_stale_share |
|:-----------|---------:|----------:|-------------:|----------------:|-------------------------:|-----------------------:|-------------------:|----------------------:|-----------------------------------:|
| Rural      |     1853 |    720382 |       225468 |           0.313 |                    0.323 |                  0.069 |              72850 |                 0.101 |                              0.007 |
| Urban      |     7914 |    348772 |        38025 |           0.109 |                    0.16  |                  0.022 |               6068 |                 0.017 |                              0     |

### edit age by tribal
| tribal     |   tracts |   road_km |   unnamed_km |   unnamed_share |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_km |   unnamed_stale_share |   median_tract_unnamed_stale_share |
|:-----------|---------:|----------:|-------------:|----------------:|-------------------------:|-----------------------:|-------------------:|----------------------:|-----------------------------------:|
| non-tribal |     8918 |    867307 |       199407 |           0.23  |                    0.332 |                  0.044 |              66272 |                 0.076 |                                  0 |
| tribal     |      874 |    202443 |        64365 |           0.318 |                    0.198 |                  0.084 |              12713 |                 0.063 |                                  0 |

### edit age by svi_q
| svi_q   |   tracts |   road_km |   unnamed_km |   unnamed_share |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_km |   unnamed_stale_share |   median_tract_unnamed_stale_share |
|:--------|---------:|----------:|-------------:|----------------:|-------------------------:|-----------------------:|-------------------:|----------------------:|-----------------------------------:|
| Q1 low  |     2448 |    189717 |        27406 |           0.144 |                    0.221 |                  0.026 |               6066 |                 0.032 |                                  0 |
| Q2      |     2448 |    344902 |        87289 |           0.253 |                    0.277 |                  0.056 |              24197 |                 0.07  |                                  0 |
| Q3      |     2448 |    343091 |        98838 |           0.288 |                    0.318 |                  0.065 |              31473 |                 0.092 |                                  0 |
| Q4 high |     2448 |    192041 |        50239 |           0.262 |                    0.343 |                  0.046 |              17248 |                 0.09  |                                  0 |

### edit age by whp_q
| whp_q   |   tracts |   road_km |   unnamed_km |   unnamed_share |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_km |   unnamed_stale_share |   median_tract_unnamed_stale_share |
|:--------|---------:|----------:|-------------:|----------------:|-------------------------:|-----------------------:|-------------------:|----------------------:|-----------------------------------:|
| Q1 low  |     2448 |     70575 |         5811 |           0.082 |                    0.022 |                  0.022 |                128 |                 0.002 |                                  0 |
| Q2      |     2448 |    152341 |        38156 |           0.25  |                    0.351 |                  0.04  |              13395 |                 0.088 |                                  0 |
| Q3      |     2448 |    298042 |        79134 |           0.266 |                    0.293 |                  0.044 |              23163 |                 0.078 |                                  0 |
| Q4 high |     2448 |    548794 |       140672 |           0.256 |                    0.301 |                  0.062 |              42298 |                 0.077 |                                  0 |

### region x urban/rural: share of unnamed km unedited since 2011 vs share of named km
|                               |   tracts |   road_km |   stale_share_of_unnamed |   stale_share_of_named |   unnamed_stale_share |
|:------------------------------|---------:|----------:|-------------------------:|-----------------------:|----------------------:|
| ('eastern-ok', 'Rural')       |      411 |    175598 |                    0.193 |                  0.105 |                 0.071 |
| ('eastern-ok', 'Urban')       |      780 |     37699 |                    0.102 |                  0.031 |                 0.013 |
| ('eastern-wa', 'Rural')       |      141 |     64806 |                    0.093 |                  0.007 |                 0.008 |
| ('eastern-wa', 'Urban')       |      273 |     14344 |                    0.002 |                  0     |                 0     |
| ('maricopa-az', 'Rural')      |      163 |     64578 |                    0.099 |                  0.009 |                 0.018 |
| ('maricopa-az', 'Urban')      |     1419 |     58553 |                    0.009 |                  0     |                 0     |
| ('northern-ca', 'Rural')      |      147 |     58120 |                    0.39  |                  0.06  |                 0.082 |
| ('northern-ca', 'Urban')      |      444 |     19311 |                    0.16  |                  0.012 |                 0.018 |
| ('south-central-tx', 'Rural') |      991 |    357280 |                    0.411 |                  0.083 |                 0.151 |
| ('south-central-tx', 'Urban') |     4998 |    218865 |                    0.194 |                  0.03  |                 0.024 |

## 3. The four SCORED classes (motorway/trunk/primary/secondary): km unnamed AND unedited since 2011
This is the km that enters the organiser's transport_gap numerator although nobody has edited it since the import era and it has no name.

### by region
| region           |   scored_km |   unnamed_scored_km |   stale_scored_km |   unnamed_stale_scored_km |   unnamed_stale_share_of_scored |
|:-----------------|------------:|--------------------:|------------------:|--------------------------:|--------------------------------:|
| eastern-ok       |       27952 |               14939 |                 1 |                       0.6 |                          0      |
| eastern-wa       |       12040 |                3525 |                 4 |                       3.8 |                          0.0003 |
| maricopa-az      |       22119 |                2428 |                 0 |                       0   |                          0      |
| northern-ca      |       12196 |                3619 |                 1 |                       0.1 |                          0      |
| south-central-tx |      118213 |               38515 |                36 |                      35.3 |                          0.0003 |
| ALL              |      192520 |               63026 |                42 |                      39.8 |                          0.0002 |

### by class
| class     |   scored_km |   unnamed_stale_km |   share |
|:----------|------------:|-------------------:|--------:|
| motorway  |       36340 |               31.8 |  0.0009 |
| primary   |       41744 |                1.6 |  0      |
| secondary |       86974 |                2.6 |  0      |
| trunk     |       27462 |                3.8 |  0.0001 |

### by ur_class
| ur_class   |   tracts |   scored_km |   unnamed_stale_scored_km |   share |   tracts_with_any |
|:-----------|---------:|------------:|--------------------------:|--------:|------------------:|
| Rural      |     1853 |      113851 |                      20.2 |  0.0002 |                53 |
| Urban      |     7914 |       78573 |                      18.8 |  0.0002 |                95 |

### by tribal
| tribal     |   tracts |   scored_km |   unnamed_stale_scored_km |   share |   tracts_with_any |
|:-----------|---------:|------------:|--------------------------:|--------:|------------------:|
| non-tribal |     8918 |      165514 |                      39.4 |  0.0002 |               146 |
| tribal     |      874 |       27006 |                       0.4 |  0      |                 4 |

### by svi_q
| svi_q   |   tracts |   scored_km |   unnamed_stale_scored_km |   share |   tracts_with_any |
|:--------|---------:|------------:|--------------------------:|--------:|------------------:|
| Q1 low  |     2448 |       32617 |                       1.1 |  0      |                13 |
| Q2      |     2448 |       58830 |                       6.4 |  0.0001 |                28 |
| Q3      |     2448 |       61882 |                      16.9 |  0.0003 |                59 |
| Q4 high |     2448 |       39192 |                      15.5 |  0.0004 |                50 |

Total scored-class km that is unnamed and unedited since 2011: 39.9 km of 192,520 scored km (0.02%); tracts with any such km: 150 of 9,792.
For comparison, unnamed-and-unedited km in the MINOR classes (tertiary/unclassified/residential): 78,944 km.

## 4. Unnamed share by scorecard stratum (supporting evidence; n tracts and km per row)

### by region
| region           |   tracts |   road_km |   unnamed_share |   unnamed_res_share |   unnamed_stale_share |   nosurface_share |   nospeed_named_share |   median_tract_unnamed_share |
|:-----------------|---------:|----------:|----------------:|--------------------:|----------------------:|------------------:|----------------------:|-----------------------------:|
| eastern-ok       |     1192 |    213301 |           0.326 |               0.247 |                 0.061 |             0.772 |                 0.414 |                        0.101 |
| eastern-wa       |      415 |     79164 |           0.088 |               0.076 |                 0.007 |             0.451 |                 0.212 |                        0.047 |
| maricopa-az      |     1593 |    123557 |           0.121 |               0.121 |                 0.01  |             0.371 |                 0.324 |                        0.025 |
| northern-ca      |      591 |     77431 |           0.187 |               0.239 |                 0.066 |             0.644 |                 0.466 |                        0.072 |
| south-central-tx |     6001 |    576297 |           0.274 |               0.281 |                 0.102 |             0.75  |                 0.584 |                        0.061 |

### by ur_class
| ur_class   |   tracts |   road_km |   unnamed_share |   unnamed_res_share |   unnamed_stale_share |   nosurface_share |   nospeed_named_share |   median_tract_unnamed_share |
|:-----------|---------:|----------:|----------------:|--------------------:|----------------------:|------------------:|----------------------:|-----------------------------:|
| Rural      |     1853 |    720382 |           0.313 |               0.33  |                 0.101 |             0.7   |                 0.527 |                        0.191 |
| Urban      |     7914 |    348772 |           0.109 |               0.086 |                 0.017 |             0.641 |                 0.459 |                        0.041 |

### by tribal
| tribal     |   tracts |   road_km |   unnamed_share |   unnamed_res_share |   unnamed_stale_share |   nosurface_share |   nospeed_named_share |   median_tract_unnamed_share |
|:-----------|---------:|----------:|----------------:|--------------------:|----------------------:|------------------:|----------------------:|-----------------------------:|
| non-tribal |     8918 |    867307 |           0.23  |               0.243 |                 0.076 |             0.667 |                 0.513 |                        0.052 |
| tribal     |      874 |    202443 |           0.318 |               0.265 |                 0.063 |             0.74  |                 0.411 |                        0.139 |

### by svi_q
| svi_q   |   tracts |   road_km |   unnamed_share |   unnamed_res_share |   unnamed_stale_share |   nosurface_share |   nospeed_named_share |   median_tract_unnamed_share |
|:--------|---------:|----------:|----------------:|--------------------:|----------------------:|------------------:|----------------------:|-----------------------------:|
| Q1 low  |     2448 |    189717 |           0.144 |               0.136 |                 0.032 |             0.593 |                 0.401 |                        0.038 |
| Q2      |     2448 |    344902 |           0.253 |               0.241 |                 0.07  |             0.68  |                 0.498 |                        0.066 |
| Q3      |     2448 |    343091 |           0.288 |               0.292 |                 0.092 |             0.706 |                 0.513 |                        0.068 |
| Q4 high |     2448 |    192041 |           0.262 |               0.293 |                 0.09  |             0.726 |                 0.559 |                        0.059 |

### by whp_q
| whp_q   |   tracts |   road_km |   unnamed_share |   unnamed_res_share |   unnamed_stale_share |   nosurface_share |   nospeed_named_share |   median_tract_unnamed_share |
|:--------|---------:|----------:|----------------:|--------------------:|----------------------:|------------------:|----------------------:|-----------------------------:|
| Q1 low  |     2448 |     70575 |           0.082 |               0.033 |                 0.002 |             0.673 |                 0.52  |                        0.031 |
| Q2      |     2448 |    152341 |           0.25  |               0.259 |                 0.088 |             0.704 |                 0.484 |                        0.047 |
| Q3      |     2448 |    298042 |           0.266 |               0.266 |                 0.078 |             0.694 |                 0.492 |                        0.065 |
| Q4 high |     2448 |    548794 |           0.256 |               0.26  |                 0.077 |             0.668 |                 0.504 |                        0.099 |

### tribal x urban/rural (unnamed share of residential km; median tract share)
|                         |   tracts |   unnamed_res_share |   median_tract_unnamed_share |   median_tract_unnamed_stale_share |         pop |
|:------------------------|---------:|--------------------:|-----------------------------:|-----------------------------------:|------------:|
| ('Rural', 'non-tribal') |     1432 |               0.343 |                        0.17  |                              0.008 | 5.08699e+06 |
| ('Rural', 'tribal')     |      421 |               0.291 |                        0.269 |                              0.005 | 1.3749e+06  |
| ('Urban', 'non-tribal') |     7461 |               0.085 |                        0.04  |                              0     | 3.2407e+07  |
| ('Urban', 'tribal')     |      453 |               0.1   |                        0.058 |                              0     | 1.55846e+06 |

### region x tribal (unnamed share of residential km)
|                                    |   tracts |   unnamed_res_share |              pop |
|:-----------------------------------|---------:|--------------------:|-----------------:|
| ('eastern-ok', 'non-tribal')       |      387 |               0.198 |      1.25302e+06 |
| ('eastern-ok', 'tribal')           |      805 |               0.256 |      2.67344e+06 |
| ('eastern-wa', 'non-tribal')       |      399 |               0.045 |      1.61368e+06 |
| ('eastern-wa', 'tribal')           |       16 |               0.321 |  63233           |
| ('maricopa-az', 'non-tribal')      |     1556 |               0.098 |      6.47822e+06 |
| ('maricopa-az', 'tribal')          |       37 |               0.378 | 128271           |
| ('northern-ca', 'non-tribal')      |      576 |               0.232 |      2.39539e+06 |
| ('northern-ca', 'tribal')          |       15 |               0.371 |  63502           |
| ('south-central-tx', 'non-tribal') |     6000 |               0.281 |      2.57537e+07 |
| ('south-central-tx', 'tribal')     |        1 |               0.185 |   4909           |

## 5. Within-region comparisons (rural tracts only): medians and Mann-Whitney U (two-sided)
| region           | comparison                                                                                  |   n_a |   n_b |   median_unnamed_share_a |   median_unnamed_share_b | p_unnamed   |   median_unnamed_stale_share_a |   median_unnamed_stale_share_b | p_unnamed_stale   |
|:-----------------|:--------------------------------------------------------------------------------------------|------:|------:|-------------------------:|-------------------------:|:------------|-------------------------------:|-------------------------------:|:------------------|
| eastern-ok       | tribal vs non-tribal                                                                        |   376 |    35 |                    0.281 |                    0.241 | 1.37e-01    |                          0.005 |                          0     | 5.55e-02          |
| eastern-wa       | tribal vs non-tribal                                                                        |    11 |   130 |                    0.109 |                    0.069 | 8.03e-02    |                          0     |                          0     | 5.53e-03          |
| maricopa-az      | tribal vs non-tribal                                                                        |    27 |   136 |                    0.166 |                    0.098 | 4.89e-03    |                          0.004 |                          0     | 8.44e-03          |
| northern-ca      | tribal vs non-tribal                                                                        |     7 |   140 |                    0.073 |                    0.138 | 8.76e-01    |                          0.006 |                          0.023 | 7.67e-01          |
| south-central-tx | tribal vs non-tribal                                                                        |     0 |   991 |                  nan     |                    0.21  | n too small |                        nan     |                          0.016 | n too small       |
| south-central-tx | border colonia belt (Maverick, Zapata, Brooks, Kinney, Zavala, Edwards) vs rest of rural TX |     6 |   985 |                    0.862 |                    0.208 | 2.54e-05    |                          0.585 |                          0.016 | 2.53e-05          |
| eastern-ok       | Cheyenne-Arapaho / Choctaw OTSA tracts vs rural tracts outside any AIANNH area              |    79 |    35 |                    0.343 |                    0.241 | 2.41e-03    |                          0.032 |                          0     | 6.16e-04          |

(a = first-named group, b = second; shares are per-tract fractions of drivable road km; 'n too small' when a group has < 5 tracts.)

## 6. WLS (weights = road km), region fixed effects — descriptive pooled test

### dependent: unnamed_share

=================================================================================================
                                    coef    std err          z      P>|z|      [0.025      0.975]
-------------------------------------------------------------------------------------------------
Intercept                         0.4817      0.030     15.831      0.000       0.422       0.541
C(region)[T.eastern-wa]          -0.2511      0.020    -12.413      0.000      -0.291      -0.211
C(region)[T.maricopa-az]         -0.1529      0.018     -8.411      0.000      -0.189      -0.117
C(region)[T.northern-ca]         -0.1073      0.022     -4.791      0.000      -0.151      -0.063
C(region)[T.south-central-tx]    -0.0022      0.018     -0.117      0.907      -0.038       0.034
rural                            -0.0706      0.017     -4.144      0.000      -0.104      -0.037
is_tribal                         0.0099      0.018      0.559      0.576      -0.025       0.045
svi_overall                       0.0855      0.015      5.614      0.000       0.056       0.115
log_density                      -0.0627      0.004    -15.042      0.000      -0.071      -0.054
whp                           -1.954e-05   4.27e-06     -4.575      0.000   -2.79e-05   -1.12e-05
=================================================================================================
n = 9706, R2 = 0.546  (tracts dropped for missing SVI: 86)

### dependent: unnamed_stale_share

=================================================================================================
                                    coef    std err          z      P>|z|      [0.025      0.975]
-------------------------------------------------------------------------------------------------
Intercept                         0.2000      0.029      6.951      0.000       0.144       0.256
C(region)[T.eastern-wa]          -0.0694      0.016     -4.240      0.000      -0.101      -0.037
C(region)[T.maricopa-az]         -0.0340      0.016     -2.110      0.035      -0.066      -0.002
C(region)[T.northern-ca]          0.0122      0.019      0.652      0.514      -0.025       0.049
C(region)[T.south-central-tx]     0.0614      0.017      3.549      0.000       0.027       0.095
rural                            -0.0791      0.015     -5.276      0.000      -0.109      -0.050
is_tribal                         0.0009      0.016      0.055      0.956      -0.030       0.031
svi_overall                       0.0362      0.013      2.856      0.004       0.011       0.061
log_density                      -0.0388      0.004     -9.793      0.000      -0.047      -0.031
whp                           -8.034e-06   2.71e-06     -2.963      0.003   -1.33e-05   -2.72e-06
=================================================================================================
n = 9706, R2 = 0.377  (tracts dropped for missing SVI: 86)

## 7. Import-era tracts: >= X % of drivable km is unnamed AND unedited since 2011 (self-constructed stratum)
| threshold   |   tracts |    pop | pop_share   | tribal_pop_share   |   overrep_vs_all |   rural_tracts |   median_svi |   pop_in_svi_top_decile |   counties |   road_km |   unnamed_stale_km |   scored_km |
|:------------|---------:|-------:|:------------|:-------------------|-----------------:|---------------:|-------------:|------------------------:|-----------:|----------:|-------------------:|------------:|
| >= 30%      |       65 | 165593 | 0.41%       | 12.4%              |             1.71 |             56 |        0.716 |                   31067 |         44 |     87933 |              39956 |        9132 |
| >= 50%      |       15 |  33043 | 0.08%       | 0.3%               |             0.04 |             11 |        0.811 |                    7318 |         12 |     29550 |              17561 |        2528 |
| >= 70%      |        0 |      0 | 0.00%       | 0.0%               |             0    |              0 |      nan     |                       0 |          0 |         0 |                  0 |           0 |

(five-region population 40,427,337; tribal share of population overall 7.3%; median tract SVI overall 0.613)

### Import-era tracts at the 50 % threshold: 15 tracts, 33,043 people

#### by region x tribal
|                                    |   tracts |   pop |   road_km |   unnamed_stale_km |
|:-----------------------------------|---------:|------:|----------:|-------------------:|
| ('maricopa-az', 'tribal')          |        1 |    88 |        51 |                 31 |
| ('south-central-tx', 'non-tribal') |       14 | 32955 |     29500 |              17531 |

#### by county (all counties with an import-era tract)
|                                      |   tracts |   pop |   road_km |   unnamed_stale_km |   median_svi | aiannh                            |
|:-------------------------------------|---------:|------:|----------:|-------------------:|-------------:|:----------------------------------|
| ('south-central-tx', 'TX Frio')      |        2 |  6323 |   1351.1  |             820.39 |         0.79 |                                   |
| ('south-central-tx', 'TX Maverick')  |        1 |  5574 |   1796.61 |            1220.39 |         0.91 |                                   |
| ('south-central-tx', 'TX Zavala')    |        3 |  4082 |   2995.81 |            1781.79 |         0.88 |                                   |
| ('south-central-tx', 'TX Sutton')    |        1 |  3372 |   3159.06 |            1689.77 |         0.85 |                                   |
| ('south-central-tx', 'TX Kinney')    |        1 |  3129 |   3810.82 |            2169.38 |         0.71 |                                   |
| ('south-central-tx', 'TX Jim Hogg')  |        1 |  2746 |   2550.37 |            1674.04 |         0.81 |                                   |
| ('south-central-tx', 'TX Uvalde')    |        1 |  2440 |   2112.42 |            1097.27 |         0.48 |                                   |
| ('south-central-tx', 'TX Dimmit')    |        1 |  2357 |   1546.33 |             895.92 |         0.87 |                                   |
| ('south-central-tx', 'TX Edwards')   |        1 |  1422 |   4696.81 |            2818.14 |         0.72 |                                   |
| ('south-central-tx', 'TX Stonewall') |        1 |  1245 |   3113.62 |            1784.91 |         0.55 |                                   |
| ('south-central-tx', 'TX King')      |        1 |   265 |   2366.67 |            1578.61 |         0.49 |                                   |
| ('maricopa-az', 'AZ Maricopa')       |        1 |    88 |     50.66 |              30.89 |         0.23 | Tohono O'odham Nation Reservation |

#### population of import-era tracts by SVI decile (1 = least vulnerable), vs the five-region population
|   svi_decile |   import_era_pop |     all_pop |   import_era_share |   all_share |   ratio |
|-------------:|-----------------:|------------:|-------------------:|------------:|--------:|
|            1 |                0 | 3.17727e+06 |              0     |       0.079 |    0    |
|            2 |                0 | 3.15526e+06 |              0     |       0.078 |    0    |
|            3 |               88 | 3.54631e+06 |              0.003 |       0.088 |    0.03 |
|            4 |                0 | 3.2901e+06  |              0     |       0.082 |    0    |
|            5 |             2705 | 3.33817e+06 |              0.082 |       0.083 |    0.99 |
|            6 |             1245 | 3.62028e+06 |              0.038 |       0.09  |    0.42 |
|            7 |                0 | 4.35849e+06 |              0     |       0.108 |    0    |
|            8 |             8245 | 4.70167e+06 |              0.25  |       0.117 |    2.14 |
|            9 |            13442 | 5.21518e+06 |              0.407 |       0.129 |    3.16 |
|           10 |             7318 | 5.9398e+06  |              0.221 |       0.147 |    1.5  |

#### hazard exposure of import-era tracts (medians) vs all tracts in the same region
| region           |   import_era_tracts |   epht_heat_days_summer_import_era |   epht_heat_days_summer_region |   usdm_summer_dsci_import_era |   usdm_summer_dsci_region |   usfs_WHP_mean_import_era |   usfs_WHP_mean_region |   svi_overall_import_era |   svi_overall_region |
|:-----------------|--------------------:|-----------------------------------:|-------------------------------:|------------------------------:|--------------------------:|---------------------------:|-----------------------:|-------------------------:|---------------------:|
| maricopa-az      |                   1 |                              14    |                          15.11 |                        159.64 |                    175.59 |                      18.03 |                  66.06 |                     0.23 |                 0.52 |
| south-central-tx |                  14 |                              15.61 |                          15.22 |                        149.38 |                     85.21 |                      34.08 |                  18.85 |                     0.83 |                 0.63 |

#### all import-era tracts (50 % threshold), sorted by population
|       GEOID | where                                           | ur_class   |   pop_total |   road_km |   unnamed_share |   unnamed_stale_share |   named_km |   svi_overall |   epht_heat_days_summer |   usdm_summer_dsci |   usfs_WHP_mean |
|------------:|:------------------------------------------------|:-----------|------------:|----------:|----------------:|----------------------:|-----------:|--------------:|------------------------:|-------------------:|----------------:|
| 48323950701 | TX Maverick                                     | Urban      |        5574 |  1796.61  |           0.926 |                 0.679 |    124.696 |         0.909 |                  15.778 |            167.534 |          13.011 |
| 48163950202 | TX Frio                                         | Urban      |        3694 |   593.994 |           0.795 |                 0.659 |     58.487 |         0.7   |                  15.889 |            145.018 |          70.734 |
| 48435950300 | TX Sutton                                       | Rural      |        3372 |  3159.06  |           0.826 |                 0.535 |    354.297 |         0.854 |                  15.444 |             99.358 |         119.339 |
| 48271950100 | TX Kinney                                       | Rural      |        3129 |  3810.82  |           0.869 |                 0.569 |    277.934 |         0.714 |                  15.889 |            144.751 |          10.036 |
| 48247950400 | TX Jim Hogg                                     | Rural      |        2746 |  2550.37  |           0.848 |                 0.656 |    214.386 |         0.811 |                  15     |            112.98  |          40.68  |
| 48163950201 | TX Frio                                         | Urban      |        2629 |   757.109 |           0.785 |                 0.566 |     96.127 |         0.874 |                  15.667 |            140.994 |          67.598 |
| 48463950201 | TX Uvalde                                       | Rural      |        2440 |  2112.42  |           0.776 |                 0.519 |    232.617 |         0.484 |                  15.444 |            159.688 |          19.579 |
| 48127950202 | TX Dimmit                                       | Rural      |        2357 |  1546.33  |           0.837 |                 0.579 |     94.908 |         0.871 |                  15.556 |            182.052 |          19.191 |
| 48507950301 | TX Zavala                                       | Urban      |        1744 |  1390.17  |           0.831 |                 0.554 |    125.653 |         0.992 |                  15.778 |            171.481 |          33.466 |
| 48507950200 | TX Zavala                                       | Rural      |        1483 |   831.057 |           0.829 |                 0.607 |     67.057 |         0.858 |                  15.889 |            166.822 |          21.635 |
| 48137950300 | TX Edwards                                      | Rural      |        1422 |  4696.81  |           0.863 |                 0.6   |    363.071 |         0.72  |                  15.444 |            125.929 |          34.696 |
| 48433950300 | TX Stonewall                                    | Rural      |        1245 |  3113.62  |           0.754 |                 0.573 |    222.884 |         0.554 |                  13.444 |            121.021 |         247.307 |
| 48507950100 | TX Zavala                                       | Rural      |         855 |   774.584 |           0.887 |                 0.654 |    153.86  |         0.875 |                  15.778 |            156.918 |          30.219 |
| 48269950100 | TX King                                         | Rural      |         265 |  2366.67  |           0.862 |                 0.667 |    142.096 |         0.49  |                  13.556 |            153.749 |         912.232 |
| 04013940700 | AZ Maricopa — Tohono O'odham Nation Reservation | Rural      |          88 |    50.657 |           0.81  |                 0.61  |      0     |         0.231 |                  14     |            159.643 |          18.032 |

## 8. Named tracts

### 8a. Most affected populated tracts (pop >= 1000), ranked by unnamed road km (area-biased: large ranch tracts)
|       GEOID | where                                 | ur_class   |   pop_total |   road_km |   unnamed_km |   unnamed_share |   unnamed_stale_share |   svi_overall |   svi_decile |   epht_heat_days_summer |   usdm_summer_dsci |   usfs_WHP_mean |
|------------:|:--------------------------------------|:-----------|------------:|----------:|-------------:|----------------:|----------------------:|--------------:|-------------:|------------------------:|-------------------:|----------------:|
| 48137950300 | TX Edwards                            | Rural      |        1422 |   4696.81 |      4052.13 |           0.863 |                 0.6   |         0.72  |            8 |                  15.444 |            125.929 |          34.696 |
| 48479001710 | TX Webb                               | Rural      |        1258 |   4260.4  |      3328.94 |           0.781 |                 0.459 |         0.693 |            7 |                  14.778 |            139.74  |          11.898 |
| 48271950100 | TX Kinney                             | Rural      |        3129 |   3810.82 |      3310.76 |           0.869 |                 0.569 |         0.714 |            8 |                  15.889 |            144.751 |          10.036 |
| 48435950300 | TX Sutton                             | Rural      |        3372 |   3159.06 |      2610.01 |           0.826 |                 0.535 |         0.854 |            9 |                  15.444 |             99.358 |         119.339 |
| 48433950300 | TX Stonewall                          | Rural      |        1245 |   3113.62 |      2348.93 |           0.754 |                 0.573 |         0.554 |            6 |                  13.444 |            121.021 |         247.307 |
| 48247950400 | TX Jim Hogg                           | Rural      |        2746 |   2550.37 |      2163.54 |           0.848 |                 0.656 |         0.811 |            9 |                  15     |            112.98  |          40.68  |
| 48505950402 | TX Zapata                             | Rural      |        2567 |   2285.18 |      1967.33 |           0.861 |                 0.457 |         0.978 |           10 |                  14.889 |            135.978 |          47.525 |
| 48047950100 | TX Brooks                             | Rural      |        2236 |   2052.49 |      1755.58 |           0.855 |                 0.489 |         0.911 |           10 |                  15.111 |             87.748 |          44.642 |
| 48319950200 | TX Mason                              | Rural      |        1784 |   2715.97 |      1745.32 |           0.643 |                 0.373 |         0.278 |            3 |                  15.222 |            154.578 |          45.172 |
| 48323950701 | TX Maverick                           | Urban      |        5574 |   1796.61 |      1663.92 |           0.926 |                 0.679 |         0.909 |           10 |                  15.778 |            167.534 |          13.011 |
| 48463950201 | TX Uvalde                             | Rural      |        2440 |   2112.42 |      1639.31 |           0.776 |                 0.519 |         0.484 |            5 |                  15.444 |            159.688 |          19.579 |
| 40093955200 | OK Major                              | Rural      |        1718 |   2460.04 |      1514.91 |           0.616 |                 0.415 |         0.178 |            2 |                   9.667 |            161.674 |         120.184 |
| 48465950802 | TX Val Verde                          | Rural      |        1933 |   2305.99 |      1464.32 |           0.635 |                 0.376 |         0.744 |            8 |                  15     |            129.183 |         108.478 |
| 48169950102 | TX Garza                              | Rural      |        2901 |   2072.72 |      1460.61 |           0.705 |                 0.428 |         0.665 |            7 |                  14.889 |            142.15  |         297.76  |
| 40039961000 | OK Custer — Cheyenne and Arapaho OTSA | Rural      |        3270 |   2153.03 |      1452.59 |           0.675 |                 0.231 |         0.67  |            7 |                  10.111 |            158.312 |          80.042 |

### 8b. Populated tracts (pop >= 1000, >= 20 road km) with the highest unnamed SHARE
|       GEOID | where                                   | ur_class   |   pop_total |   road_km |   unnamed_km |   unnamed_share |   unnamed_stale_share |   svi_overall |   svi_decile |   epht_heat_days_summer |   usdm_summer_dsci |   usfs_WHP_mean |
|------------:|:----------------------------------------|:-----------|------------:|----------:|-------------:|----------------:|----------------------:|--------------:|-------------:|------------------------:|-------------------:|----------------:|
| 48323950701 | TX Maverick                             | Urban      |        5574 |  1796.61  |     1663.92  |           0.926 |                 0.679 |         0.909 |           10 |                  15.778 |            167.534 |          13.011 |
| 40149965000 | OK Washita — Cheyenne and Arapaho OTSA  | Rural      |        1989 |   897.462 |      819.687 |           0.913 |                 0.094 |         0.517 |            6 |                  10.667 |            163.346 |          17.016 |
| 48427950101 | TX Starr                                | Rural      |        1040 |  1155.89  |     1020.1   |           0.883 |                 0.42  |         0.776 |            8 |                  13.889 |             89.585 |          81.735 |
| 48271950100 | TX Kinney                               | Rural      |        3129 |  3810.82  |     3310.76  |           0.869 |                 0.569 |         0.714 |            8 |                  15.889 |            144.751 |          10.036 |
| 40149965100 | OK Washita — Cheyenne and Arapaho OTSA  | Rural      |        3409 |   640.672 |      554.62  |           0.866 |                 0.032 |         0.546 |            6 |                  10.444 |            160.083 |          25.909 |
| 48137950300 | TX Edwards                              | Rural      |        1422 |  4696.81  |     4052.13  |           0.863 |                 0.6   |         0.72  |            8 |                  15.444 |            125.929 |          34.696 |
| 40149965400 | OK Washita — Cheyenne and Arapaho OTSA  | Rural      |        1750 |  1127.6   |      971.69  |           0.862 |                 0.092 |         0.52  |            6 |                  10.667 |            156.326 |          30.996 |
| 48505950402 | TX Zapata                               | Rural      |        2567 |  2285.18  |     1967.33  |           0.861 |                 0.457 |         0.978 |           10 |                  14.889 |            135.978 |          47.525 |
| 48047950100 | TX Brooks                               | Rural      |        2236 |  2052.49  |     1755.58  |           0.855 |                 0.489 |         0.911 |           10 |                  15.111 |             87.748 |          44.642 |
| 48247950400 | TX Jim Hogg                             | Rural      |        2746 |  2550.37  |     2163.54  |           0.848 |                 0.656 |         0.811 |            9 |                  15     |            112.98  |          40.68  |
| 48127950202 | TX Dimmit                               | Rural      |        2357 |  1546.33  |     1294.45  |           0.837 |                 0.579 |         0.871 |            9 |                  15.556 |            182.052 |          19.191 |
| 48507950301 | TX Zavala                               | Urban      |        1744 |  1390.17  |     1154.61  |           0.831 |                 0.554 |         0.992 |           10 |                  15.778 |            171.481 |          33.466 |
| 48507950200 | TX Zavala                               | Rural      |        1483 |   831.057 |      688.881 |           0.829 |                 0.607 |         0.858 |            9 |                  15.889 |            166.822 |          21.635 |
| 48435950300 | TX Sutton                               | Rural      |        3372 |  3159.06  |     2610.01  |           0.826 |                 0.535 |         0.854 |            9 |                  15.444 |             99.358 |         119.339 |
| 48323950207 | TX Maverick — Kickapoo (TX) Reservation | Urban      |        4614 |  1249.99  |     1025.61  |           0.82  |                 0.342 |         0.94  |           10 |                  15.111 |            183.98  |           9.222 |

### 8c. Populated tracts (pop >= 1000, >= 20 road km) with the highest unnamed-AND-unedited (import-era) share
|       GEOID | where                    | ur_class   |   pop_total |   road_km |   unnamed_km |   unnamed_share |   unnamed_stale_share |   svi_overall |   svi_decile |   epht_heat_days_summer |   usdm_summer_dsci |   usfs_WHP_mean |
|------------:|:-------------------------|:-----------|------------:|----------:|-------------:|----------------:|----------------------:|--------------:|-------------:|------------------------:|-------------------:|----------------:|
| 48323950701 | TX Maverick              | Urban      |        5574 |  1796.61  |     1663.92  |           0.926 |                 0.679 |         0.909 |           10 |                  15.778 |            167.534 |          13.011 |
| 48163950202 | TX Frio                  | Urban      |        3694 |   593.994 |      472.104 |           0.795 |                 0.659 |         0.7   |            8 |                  15.889 |            145.018 |          70.734 |
| 48247950400 | TX Jim Hogg              | Rural      |        2746 |  2550.37  |     2163.54  |           0.848 |                 0.656 |         0.811 |            9 |                  15     |            112.98  |          40.68  |
| 48507950200 | TX Zavala                | Rural      |        1483 |   831.057 |      688.881 |           0.829 |                 0.607 |         0.858 |            9 |                  15.889 |            166.822 |          21.635 |
| 48137950300 | TX Edwards               | Rural      |        1422 |  4696.81  |     4052.13  |           0.863 |                 0.6   |         0.72  |            8 |                  15.444 |            125.929 |          34.696 |
| 48127950202 | TX Dimmit                | Rural      |        2357 |  1546.33  |     1294.45  |           0.837 |                 0.579 |         0.871 |            9 |                  15.556 |            182.052 |          19.191 |
| 48433950300 | TX Stonewall             | Rural      |        1245 |  3113.62  |     2348.93  |           0.754 |                 0.573 |         0.554 |            6 |                  13.444 |            121.021 |         247.307 |
| 48271950100 | TX Kinney                | Rural      |        3129 |  3810.82  |     3310.76  |           0.869 |                 0.569 |         0.714 |            8 |                  15.889 |            144.751 |          10.036 |
| 48163950201 | TX Frio                  | Urban      |        2629 |   757.109 |      594.232 |           0.785 |                 0.566 |         0.874 |            9 |                  15.667 |            140.994 |          67.598 |
| 48507950301 | TX Zavala                | Urban      |        1744 |  1390.17  |     1154.61  |           0.831 |                 0.554 |         0.992 |           10 |                  15.778 |            171.481 |          33.466 |
| 48435950300 | TX Sutton                | Rural      |        3372 |  3159.06  |     2610.01  |           0.826 |                 0.535 |         0.854 |            9 |                  15.444 |             99.358 |         119.339 |
| 48463950201 | TX Uvalde                | Rural      |        2440 |  2112.42  |     1639.31  |           0.776 |                 0.519 |         0.484 |            5 |                  15.444 |            159.688 |          19.579 |
| 48463950202 | TX Uvalde                | Rural      |        4679 |   527.491 |      376.811 |           0.714 |                 0.49  |         0.993 |           10 |                  15.667 |            163.662 |          26.241 |
| 48047950100 | TX Brooks                | Rural      |        2236 |  2052.49  |     1755.58  |           0.855 |                 0.489 |         0.911 |           10 |                  15.111 |             87.748 |          44.642 |
| 40107080700 | OK Okfuskee — Creek OTSA | Rural      |        3125 |   770.823 |      453.484 |           0.588 |                 0.47  |         0.765 |            8 |                  10.778 |             32.648 |         160.633 |

## 9. Named clusters: hazard and vulnerability columns from the challenge strata table (medians over the cluster's tracts)
| cluster                                                                        |   tracts |    pop |   road_km |   unnamed_share_kmw |   unnamed_stale_share_kmw |   import_era_tracts(>=50%) |   median_svi |   svi_region_median |   median_heat_days_summer |   heat_region_median |   median_summer_dsci |   dsci_region_median |   median_whp |   whp_region_median |
|:-------------------------------------------------------------------------------|---------:|-------:|----------:|--------------------:|--------------------------:|---------------------------:|-------------:|--------------------:|--------------------------:|---------------------:|---------------------:|---------------------:|-------------:|--------------------:|
| Maverick County TX (all scored tracts)                                         |       13 |  57887 |      3786 |               0.786 |                     0.465 |                          1 |        0.922 |               0.635 |                      15.3 |                 15.2 |                172.6 |                 85.2 |          0.9 |                18.8 |
| Maverick: 48323950701 + 48323950207 (east of Eagle Pass; Kickapoo Reservation) |        2 |  10188 |      3046 |               0.883 |                     0.541 |                          1 |        0.925 |               0.635 |                      15.4 |                 15.2 |                175.8 |                 85.2 |         11.1 |                18.8 |
| Zapata County TX                                                               |        6 |  13889 |      2490 |               0.796 |                     0.421 |                          0 |        0.948 |               0.635 |                      14.7 |                 15.2 |                140.4 |                 85.2 |         26.1 |                18.8 |
| Brooks County TX                                                               |        2 |   7076 |      2147 |               0.82  |                     0.467 |                          0 |        0.895 |               0.635 |                      14.9 |                 15.2 |                 86.1 |                 85.2 |         35.3 |                18.8 |
| Kinney County TX                                                               |        1 |   3129 |      3810 |               0.869 |                     0.569 |                          1 |        0.714 |               0.635 |                      15.9 |                 15.2 |                144.8 |                 85.2 |         10   |                18.8 |
| Zavala County TX                                                               |        4 |   9670 |      3082 |               0.825 |                     0.581 |                          3 |        0.866 |               0.635 |                      15.8 |                 15.2 |                169.2 |                 85.2 |         25.9 |                18.8 |
| Edwards County TX                                                              |        1 |   1422 |      4696 |               0.863 |                     0.6   |                          1 |        0.72  |               0.635 |                      15.4 |                 15.2 |                125.9 |                 85.2 |         34.7 |                18.8 |
| Cheyenne and Arapaho OTSA, Washita County OK (40149965000/965100/965400)       |        3 |   7148 |      2665 |               0.88  |                     0.078 |                          0 |        0.52  |               0.615 |                      10.7 |                 11.3 |                160.1 |                 63.3 |         25.9 |                12.6 |
| Cheyenne and Arapaho OTSA (all tracts)                                         |       57 | 214569 |     27591 |               0.474 |                     0.129 |                          0 |        0.522 |               0.615 |                      10.9 |                 11.3 |                122.1 |                 63.3 |         25.9 |                12.6 |
| Choctaw OTSA (all tracts)                                                      |       67 | 223362 |     26182 |               0.337 |                     0.055 |                          0 |        0.746 |               0.615 |                      11.9 |                 11.3 |                 40.9 |                 63.3 |        128.2 |                12.6 |

Column meanings (challenge strata table): epht_heat_days_summer = CDC EPHT extreme-heat days per summer; usdm_summer_dsci = US Drought Monitor summer Drought Severity and Coverage Index (0-500); usfs_WHP_mean = USFS Wildfire Hazard Potential (mean); svi_overall = CDC SVI 2022 overall percentile rank.

## 10. Tracts with >= 50 % of road km unnamed (any edit age): counts and population
|                                    |   tracts |    pop |
|:-----------------------------------|---------:|-------:|
| ('eastern-ok', 'non-tribal')       |        6 |  14367 |
| ('eastern-ok', 'tribal')           |       49 | 127362 |
| ('maricopa-az', 'non-tribal')      |        4 |   2064 |
| ('maricopa-az', 'tribal')          |        1 |     88 |
| ('northern-ca', 'non-tribal')      |        4 |  11711 |
| ('south-central-tx', 'non-tribal') |       82 | 237715 |

People living in tracts where >= 50 % of drivable road km is unnamed: 393307 (1.0% of regional population); tribal share of those people: 32.4% vs tribal share overall 7.3%
