# Official Benchmark Summary

Generated from append-only raw JSONL. Missing cells are never estimated.

## Ingest

| Target | Status | End-to-ready s | All nodes/s | Relationships/s |
|---|---|---:|---:|---:|
| cognodb-c0 | complete | 580.690 | 17.827 | 173.649 |
| neo4j-aura-free | missing | missing | missing | missing |
| neo4j-ce-capped | complete | 218.569 | 47.363 | 461.346 |
| memgraph-capped | complete | 291.171 | 35.553 | 346.312 |
| falkordb-capped | complete | 53.175 | 194.678 | 1896.301 |
| arangodb-capped | complete | 76.282 | 135.707 | 1321.885 |

## Read latency

| Target | Workload | p50 ms | p95 ms | p99 ms | p50 CI95 ms | CV | Successes | Failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| cognodb-c0 | aggregation | 379.925 | 436.359 | 454.571 | 377.332-381.387 | 0.068 | 300 | 0 |
| cognodb-c0 | filtered_lookup | 145.009 | 151.473 | 155.269 | 144.562-145.726 | 0.025 | 300 | 0 |
| cognodb-c0 | hop_1 | 141.831 | 318.819 | 515.050 | 139.241-144.999 | 0.409 | 300 | 0 |
| cognodb-c0 | hop_2 | 345.776 | 1155.979 | 1700.102 | 267.738-399.494 | 0.767 | 300 | 0 |
| cognodb-c0 | hop_3 | 4201.546 | 4756.912 | 4937.562 | 4168.085-4258.019 | 0.108 | 300 | 0 |
| cognodb-c0 | point_lookup | 133.004 | 136.651 | 139.039 | 132.721-133.297 | 0.059 | 300 | 0 |
| cognodb-c0 | return_1 | 133.165 | 137.319 | 219.313 | 132.825-133.402 | 0.122 | 300 | 0 |
| neo4j-ce-capped | aggregation | 99.578 | 288.762 | 395.460 | 98.483-100.645 | 0.542 | 300 | 0 |
| neo4j-ce-capped | filtered_lookup | 20.531 | 56.281 | 80.345 | 20.136-21.028 | 0.676 | 300 | 0 |
| neo4j-ce-capped | hop_1 | 18.098 | 82.464 | 159.503 | 14.687-21.806 | 1.011 | 300 | 0 |
| neo4j-ce-capped | hop_2 | 51.998 | 111.872 | 234.374 | 48.908-54.066 | 0.708 | 300 | 0 |
| neo4j-ce-capped | hop_3 | 728.155 | 1056.435 | 1257.019 | 715.565-735.690 | 0.176 | 300 | 0 |
| neo4j-ce-capped | point_lookup | 5.184 | 32.088 | 67.852 | 4.647-5.582 | 1.392 | 300 | 0 |
| neo4j-ce-capped | return_1 | 6.326 | 41.858 | 64.334 | 5.841-6.736 | 1.227 | 300 | 0 |
| memgraph-capped | aggregation | 68.500 | 79.935 | 83.289 | 40.579-70.679 | 0.435 | 300 | 0 |
| memgraph-capped | filtered_lookup | 14.763 | 18.356 | 19.294 | 14.527-15.084 | 0.141 | 300 | 0 |
| memgraph-capped | hop_1 | 13.430 | 62.949 | 119.699 | 11.324-16.300 | 1.012 | 300 | 0 |
| memgraph-capped | hop_2 | 38.188 | 62.040 | 77.102 | 36.885-41.848 | 0.331 | 300 | 0 |
| memgraph-capped | hop_3 | 515.035 | 614.691 | 678.135 | 508.064-521.047 | 0.088 | 300 | 0 |
| memgraph-capped | point_lookup | 5.272 | 30.426 | 37.204 | 4.936-5.685 | 1.000 | 300 | 0 |
| memgraph-capped | return_1 | 2.024 | 4.938 | 5.727 | 1.845-2.316 | 0.449 | 300 | 0 |
| falkordb-capped | aggregation | 120.440 | 177.303 | 202.634 | 119.246-122.117 | 0.212 | 300 | 0 |
| falkordb-capped | filtered_lookup | 5.603 | 8.954 | 10.061 | 5.341-5.907 | 0.274 | 300 | 0 |
| falkordb-capped | hop_1 | 5.219 | 21.942 | 38.325 | 4.745-5.768 | 0.942 | 300 | 0 |
| falkordb-capped | hop_2 | 10.423 | 14.776 | 20.738 | 10.129-10.702 | 0.308 | 300 | 0 |
| falkordb-capped | hop_3 | 219.996 | 274.160 | 293.738 | 217.587-222.653 | 0.132 | 300 | 0 |
| falkordb-capped | point_lookup | 1.839 | 4.399 | 5.142 | 1.750-2.085 | 0.431 | 300 | 0 |
| falkordb-capped | return_1 | 1.609 | 4.133 | 5.904 | 1.523-1.714 | 0.508 | 300 | 0 |
| arangodb-capped | aggregation | 91.352 | 104.506 | 171.670 | 90.395-92.472 | 0.281 | 300 | 0 |
| arangodb-capped | filtered_lookup | 48.519 | 52.704 | 53.581 | 48.213-48.902 | 0.046 | 300 | 0 |
| arangodb-capped | hop_1 | 47.920 | 54.569 | 59.997 | 47.620-48.410 | 0.068 | 300 | 0 |
| arangodb-capped | hop_2 | 55.491 | 86.624 | 104.169 | 54.493-57.249 | 0.257 | 300 | 0 |
| arangodb-capped | hop_3 | 196.982 | 292.533 | 361.720 | 194.578-199.935 | 0.202 | 300 | 0 |
| arangodb-capped | point_lookup | 46.012 | 50.183 | 52.900 | 45.682-46.479 | 0.048 | 300 | 0 |
| arangodb-capped | return_1 | 45.635 | 49.520 | 51.448 | 45.372-45.910 | 0.045 | 300 | 0 |

## Traversal latency by source-degree bucket

| Target | Hop/bucket | p50 ms | p95 ms | p99 ms | Valid N | Failures |
|---|---|---:|---:|---:|---:|---:|
| cognodb-c0 | hop_1/low | 134.528 | 138.739 | 141.159 | 75 | 0 |
| cognodb-c0 | hop_1/medium | 137.241 | 144.361 | 156.681 | 75 | 0 |
| cognodb-c0 | hop_1/high | 147.565 | 159.975 | 161.886 | 75 | 0 |
| cognodb-c0 | hop_1/hub | 174.991 | 513.776 | 524.803 | 75 | 0 |
| cognodb-c0 | hop_2/low | 164.315 | 186.345 | 217.950 | 75 | 0 |
| cognodb-c0 | hop_2/medium | 211.811 | 345.754 | 365.163 | 75 | 0 |
| cognodb-c0 | hop_2/high | 501.143 | 718.904 | 773.819 | 75 | 0 |
| cognodb-c0 | hop_2/hub | 942.989 | 1667.090 | 1972.006 | 75 | 0 |
| cognodb-c0 | hop_3/low | 3683.153 | 4229.209 | 4449.697 | 75 | 0 |
| cognodb-c0 | hop_3/medium | 4060.499 | 4544.686 | 4625.928 | 75 | 0 |
| cognodb-c0 | hop_3/high | 4304.153 | 4554.914 | 4800.193 | 75 | 0 |
| cognodb-c0 | hop_3/hub | 4540.919 | 4899.643 | 5581.357 | 75 | 0 |
| neo4j-ce-capped | hop_1/low | 7.437 | 26.287 | 50.039 | 75 | 0 |
| neo4j-ce-capped | hop_1/medium | 11.644 | 17.292 | 25.108 | 75 | 0 |
| neo4j-ce-capped | hop_1/high | 25.624 | 44.037 | 67.392 | 75 | 0 |
| neo4j-ce-capped | hop_1/hub | 58.649 | 153.206 | 170.041 | 75 | 0 |
| neo4j-ce-capped | hop_2/low | 36.889 | 56.307 | 90.088 | 75 | 0 |
| neo4j-ce-capped | hop_2/medium | 42.626 | 70.679 | 109.222 | 75 | 0 |
| neo4j-ce-capped | hop_2/high | 57.519 | 106.978 | 250.131 | 75 | 0 |
| neo4j-ce-capped | hop_2/hub | 82.162 | 189.904 | 355.911 | 75 | 0 |
| neo4j-ce-capped | hop_3/low | 690.407 | 914.770 | 1077.075 | 75 | 0 |
| neo4j-ce-capped | hop_3/medium | 699.788 | 952.851 | 1257.530 | 75 | 0 |
| neo4j-ce-capped | hop_3/high | 753.760 | 1064.852 | 1269.840 | 75 | 0 |
| neo4j-ce-capped | hop_3/hub | 755.633 | 1119.946 | 1317.727 | 75 | 0 |
| memgraph-capped | hop_1/low | 6.231 | 9.651 | 11.307 | 75 | 0 |
| memgraph-capped | hop_1/medium | 9.414 | 14.512 | 17.040 | 75 | 0 |
| memgraph-capped | hop_1/high | 19.592 | 31.483 | 33.713 | 75 | 0 |
| memgraph-capped | hop_1/hub | 45.018 | 119.484 | 130.147 | 75 | 0 |
| memgraph-capped | hop_2/low | 25.603 | 36.421 | 41.699 | 75 | 0 |
| memgraph-capped | hop_2/medium | 33.275 | 40.337 | 44.269 | 75 | 0 |
| memgraph-capped | hop_2/high | 44.739 | 55.348 | 59.582 | 75 | 0 |
| memgraph-capped | hop_2/hub | 53.189 | 74.753 | 82.640 | 75 | 0 |
| memgraph-capped | hop_3/low | 496.342 | 562.587 | 603.003 | 75 | 0 |
| memgraph-capped | hop_3/medium | 501.010 | 585.355 | 646.190 | 75 | 0 |
| memgraph-capped | hop_3/high | 524.676 | 591.215 | 698.000 | 75 | 0 |
| memgraph-capped | hop_3/hub | 551.373 | 647.494 | 679.160 | 75 | 0 |
| falkordb-capped | hop_1/low | 2.360 | 5.059 | 6.163 | 75 | 0 |
| falkordb-capped | hop_1/medium | 3.403 | 5.735 | 7.590 | 75 | 0 |
| falkordb-capped | hop_1/high | 6.970 | 12.218 | 16.202 | 75 | 0 |
| falkordb-capped | hop_1/hub | 15.721 | 38.089 | 44.169 | 75 | 0 |
| falkordb-capped | hop_2/low | 8.329 | 12.508 | 18.082 | 75 | 0 |
| falkordb-capped | hop_2/medium | 10.004 | 14.703 | 23.566 | 75 | 0 |
| falkordb-capped | hop_2/high | 10.872 | 16.709 | 18.031 | 75 | 0 |
| falkordb-capped | hop_2/hub | 11.409 | 14.270 | 19.484 | 75 | 0 |
| falkordb-capped | hop_3/low | 217.234 | 267.236 | 300.572 | 75 | 0 |
| falkordb-capped | hop_3/medium | 222.264 | 256.488 | 264.279 | 75 | 0 |
| falkordb-capped | hop_3/high | 220.029 | 275.855 | 283.752 | 75 | 0 |
| falkordb-capped | hop_3/hub | 219.259 | 277.614 | 341.378 | 75 | 0 |
| arangodb-capped | hop_1/low | 46.280 | 49.231 | 49.774 | 75 | 0 |
| arangodb-capped | hop_1/medium | 47.126 | 50.711 | 51.643 | 75 | 0 |
| arangodb-capped | hop_1/high | 48.000 | 51.816 | 53.504 | 75 | 0 |
| arangodb-capped | hop_1/hub | 51.422 | 59.496 | 62.034 | 75 | 0 |
| arangodb-capped | hop_2/low | 49.163 | 53.358 | 55.733 | 75 | 0 |
| arangodb-capped | hop_2/medium | 53.497 | 60.907 | 69.393 | 75 | 0 |
| arangodb-capped | hop_2/high | 60.167 | 66.326 | 92.735 | 75 | 0 |
| arangodb-capped | hop_2/hub | 71.607 | 97.503 | 120.606 | 75 | 0 |
| arangodb-capped | hop_3/low | 192.260 | 309.886 | 383.617 | 75 | 0 |
| arangodb-capped | hop_3/medium | 194.445 | 292.142 | 323.018 | 75 | 0 |
| arangodb-capped | hop_3/high | 197.839 | 284.013 | 295.142 | 75 | 0 |
| arangodb-capped | hop_3/hub | 220.149 | 303.742 | 319.274 | 75 | 0 |

## Mixed workload

| Target | Model | Mix | Concurrency | Offered QPS | Achieved QPS | p50/p95/p99 ms | R/W attempts | Errors/timeouts |
|---|---|---|---:|---:|---:|---:|---:|---:|
| cognodb-c0 | closed_loop | read-heavy | 1 | missing | 3.779 | 141.595/1001.884/1207.151 | 211/16 | 0/0 |
| cognodb-c0 | closed_loop | read-heavy | 5 | missing | 6.491 | 257.990/3468.533/4684.755 | 384/27 | 0/0 |
| cognodb-c0 | closed_loop | read-heavy | 10 | missing | 5.041 | 445.492/9660.462/15196.844 | 312/14 | 1/0 |
| cognodb-c0 | closed_loop | read-heavy | 20 | missing | 3.266 | 799.475/9370.010/19717.748 | 290/8 | 35/0 |
| cognodb-c0 | closed_loop | read-heavy | 40 | missing | 6.926 | 1099.868/12226.032/18770.309 | 565/25 | 56/0 |
| cognodb-c0 | closed_loop | mixed | 1 | missing | 4.146 | 138.578/924.903/1130.345 | 182/67 | 0/0 |
| cognodb-c0 | closed_loop | mixed | 5 | missing | 8.162 | 226.868/2957.832/4474.825 | 395/100 | 0/0 |
| cognodb-c0 | closed_loop | mixed | 10 | missing | 5.485 | 432.784/7902.358/12107.102 | 297/72 | 3/0 |
| cognodb-c0 | closed_loop | mixed | 20 | missing | 5.172 | 690.583/10595.983/18681.137 | 308/74 | 23/0 |
| cognodb-c0 | closed_loop | mixed | 40 | missing | 7.320 | 1101.168/7598.550/18108.984 | 697/179 | 289/0 |
| cognodb-c0 | open_loop | mixed | 40 | 100 | 5.730 | 58497.800/115889.493/123178.850 | 4801/1199 | 4931/0 |
| neo4j-ce-capped | closed_loop | read-heavy | 1 | missing | 29.032 | 16.923/100.127/226.386 | 1652/90 | 0/0 |
| neo4j-ce-capped | closed_loop | read-heavy | 5 | missing | 21.322 | 119.076/749.510/1127.511 | 1202/85 | 0/0 |
| neo4j-ce-capped | closed_loop | read-heavy | 10 | missing | 22.647 | 295.424/1286.695/2239.431 | 1296/70 | 0/0 |
| neo4j-ce-capped | closed_loop | read-heavy | 20 | missing | 21.931 | 604.126/2467.262/3688.548 | 1276/65 | 0/0 |
| neo4j-ce-capped | closed_loop | read-heavy | 40 | missing | 22.936 | 635.106/4414.866/7669.832 | 1385/77 | 27/0 |
| neo4j-ce-capped | closed_loop | mixed | 1 | missing | 38.983 | 9.721/74.945/144.588 | 1841/498 | 0/0 |
| neo4j-ce-capped | closed_loop | mixed | 5 | missing | 27.852 | 81.548/567.360/902.386 | 1337/342 | 0/0 |
| neo4j-ce-capped | closed_loop | mixed | 10 | missing | 25.325 | 110.099/1231.651/2001.603 | 1227/311 | 0/0 |
| neo4j-ce-capped | closed_loop | mixed | 20 | missing | 25.301 | 291.520/2353.721/3358.246 | 1244/299 | 2/0 |
| neo4j-ce-capped | closed_loop | mixed | 40 | missing | 26.592 | 598.549/4052.482/6494.837 | 1533/428 | 311/0 |
| neo4j-ce-capped | open_loop | mixed | 40 | 100 | 25.304 | 83776.942/157185.945/164084.218 | 4801/1199 | 264/0 |
| memgraph-capped | closed_loop | read-heavy | 1 | missing | 45.763 | 10.548/56.078/79.642 | 2610/138 | 0/0 |
| memgraph-capped | closed_loop | read-heavy | 5 | missing | 30.583 | 56.635/453.518/890.445 | 1714/123 | 0/0 |
| memgraph-capped | closed_loop | read-heavy | 10 | missing | 30.500 | 112.457/900.399/2008.723 | 1737/102 | 0/0 |
| memgraph-capped | closed_loop | read-heavy | 20 | missing | 27.825 | 364.550/1937.459/2978.268 | 1601/88 | 0/0 |
| memgraph-capped | closed_loop | read-heavy | 40 | missing | 28.814 | 446.763/3992.568/6634.776 | 1681/91 | 1/0 |
| memgraph-capped | closed_loop | mixed | 1 | missing | 53.307 | 7.731/51.435/78.387 | 2532/668 | 0/0 |
| memgraph-capped | closed_loop | mixed | 5 | missing | 33.070 | 45.780/448.104/707.268 | 1594/398 | 0/0 |
| memgraph-capped | closed_loop | mixed | 10 | missing | 33.699 | 47.006/909.857/1457.202 | 1608/420 | 0/0 |
| memgraph-capped | closed_loop | mixed | 20 | missing | 32.738 | 106.862/1813.412/2937.380 | 1607/379 | 0/0 |
| memgraph-capped | closed_loop | mixed | 40 | missing | 35.506 | 140.424/3239.757/5270.121 | 1702/466 | 0/0 |
| memgraph-capped | open_loop | mixed | 40 | 100 | 31.810 | 66121.904/120853.141/126470.036 | 4801/1199 | 0/0 |
| falkordb-capped | closed_loop | read-heavy | 1 | missing | 153.897 | 4.460/11.697/24.990 | 8778/456 | 0/0 |
| falkordb-capped | closed_loop | read-heavy | 5 | missing | 203.975 | 10.218/27.995/42.931 | 11595/647 | 0/0 |
| falkordb-capped | closed_loop | read-heavy | 10 | missing | 207.397 | 10.293/27.914/43.812 | 11813/633 | 0/0 |
| falkordb-capped | closed_loop | read-heavy | 20 | missing | 205.476 | 10.229/27.331/44.355 | 11706/630 | 0/0 |
| falkordb-capped | closed_loop | read-heavy | 40 | missing | 201.707 | 10.018/28.690/48.932 | 11492/621 | 0/0 |
| falkordb-capped | closed_loop | mixed | 1 | missing | 158.790 | 3.866/11.875/24.187 | 7636/1892 | 0/0 |
| falkordb-capped | closed_loop | mixed | 5 | missing | 226.893 | 9.104/24.967/39.649 | 10870/2748 | 0/0 |
| falkordb-capped | closed_loop | mixed | 10 | missing | 221.209 | 9.113/26.541/43.369 | 10663/2612 | 0/0 |
| falkordb-capped | closed_loop | mixed | 20 | missing | 220.886 | 8.717/26.217/42.634 | 10646/2614 | 0/0 |
| falkordb-capped | closed_loop | mixed | 40 | missing | 229.910 | 8.364/24.513/40.205 | 11051/2755 | 0/0 |
| falkordb-capped | open_loop | mixed | 40 | 100 | 99.955 | 4.902/15.043/33.658 | 4801/1199 | 0/0 |
| arangodb-capped | closed_loop | read-heavy | 1 | missing | 19.314 | 47.829/70.020/98.161 | 1092/67 | 0/0 |
| arangodb-capped | closed_loop | read-heavy | 5 | missing | 53.802 | 83.859/202.616/302.703 | 3041/188 | 0/0 |
| arangodb-capped | closed_loop | read-heavy | 10 | missing | 55.448 | 178.715/375.058/484.039 | 3146/187 | 0/0 |
| arangodb-capped | closed_loop | read-heavy | 20 | missing | 52.567 | 371.408/610.337/835.519 | 3016/148 | 0/0 |
| arangodb-capped | closed_loop | read-heavy | 40 | missing | 19.333 | 2044.088/2298.937/2494.803 | 1142/57 | 0/0 |
| arangodb-capped | closed_loop | mixed | 1 | missing | 19.462 | 48.311/67.791/84.758 | 900/268 | 0/0 |
| arangodb-capped | closed_loop | mixed | 5 | missing | 51.482 | 84.393/207.438/316.323 | 2473/621 | 1/0 |
| arangodb-capped | closed_loop | mixed | 10 | missing | 56.727 | 170.124/358.997/472.369 | 2738/685 | 0/0 |
| arangodb-capped | closed_loop | mixed | 20 | missing | 55.542 | 319.358/597.416/704.927 | 2702/653 | 0/0 |
| arangodb-capped | closed_loop | mixed | 40 | missing | 19.531 | 2044.608/2146.503/2284.316 | 951/261 | 0/0 |
| arangodb-capped | open_loop | mixed | 40 | 100 | 19.604 | 122196.071/233794.242/243662.724 | 4801/1199 | 0/0 |

## Controlled resource footprint

| Target | Samples | CPU p95/max % | Memory p95/peak MiB | Data directory MiB | Filesystem used/capacity MiB |
|---|---:|---:|---:|---:|---:|
| cognodb-c0 | not observable | missing/missing | not observable/not observable | not observable | not observable/not observable |
| neo4j-aura-free | not observable | missing/missing | not observable/not observable | not observable | not observable/not observable |
| neo4j-ce-capped | 1469 | 51.085/55.941 | 509.64/510.69 | 530.85 | 531.29/973.42 |
| memgraph-capped | 1325 | 50.184/51.242 | 138.19/182.91 | 46.08 | 364.21/973.42 |
| falkordb-capped | 906 | 49.162/51.083 | 27.25/72.36 | 0.00 | 0.27/973.42 |
| arangodb-capped | 1199 | 50.627/53.505 | 434.88/458.24 | 23.57 | 90.50/973.42 |

## Unmeasured query-plan evidence

| Target | Workload | Captured | Plan operators |
|---|---|---|---|
| cognodb-c0 | point_lookup | True | ProduceResults > NodeByLabelScan |
| cognodb-c0 | filtered_lookup | True | ProduceResults > NodeIndexSeek |
| cognodb-c0 | hop_3 | True | ProduceResults > Filter > Expand > Expand > NodeByLabelScan > Projection > Expand > AllNodeScan |
| cognodb-c0 | aggregation | True | ProduceResults > Expand > AllNodeScan |
| neo4j-ce-capped | point_lookup | True | ProduceResults@neo4j > Projection@neo4j > CacheProperties@neo4j > NodeUniqueIndexSeek@neo4j |
| neo4j-ce-capped | filtered_lookup | True | ProduceResults@neo4j > Sort@neo4j > Projection@neo4j > NodeIndexSeek@neo4j |
| neo4j-ce-capped | hop_3 | True | ProduceResults@neo4j > Sort@neo4j > Distinct@neo4j > Filter@neo4j > Expand(All)@neo4j > Distinct@neo4j > Filter@neo4j > Expand(All)@neo4j > Filter@neo4j > Expand(All)@neo4j > NodeUniqueIndexSeek@neo4j |
| neo4j-ce-capped | aggregation | True | ProduceResults@neo4j > Sort@neo4j > EagerAggregation@neo4j > DirectedRelationshipTypeScan@neo4j |
| memgraph-capped | point_lookup | True | * Produce {movieId, title, year} > * Filter (movie :Movie), {movie.movieId} > * ScanAll (movie) > * Once |
| memgraph-capped | filtered_lookup | True | * OrderBy {movieId} > * Produce {movieId} > * ScanAllByLabelProperties (movie :Movie {year}) > * Once |
| memgraph-capped | hop_3 | True | * OrderBy {movieId} > * Distinct > * Produce {movieId} > * Filter (movie :Movie) > * Expand (peer)-[anon6:RATED]->(movie) > * Distinct > * Produce {peer} > * Filter (peer :User), Generic {peer} > * EdgeUniquenessFilter {anon2 : anon4} > * Expand (anon3)<-[anon4:RATED]-(peer) > * Filter (anon3 :Movie) > * Expand (anon1)-[anon2:RATED]->(anon3) > * Filter (anon1 :User), {anon1.userId} > * ScanAll (anon1) > * Once |
| memgraph-capped | aggregation | True | * OrderBy {rating, count} > * Produce {rating, count} > * Aggregate {COUNT-1} {rating} > * Expand (anon1)-[rating:RATED]->(anon2) > * ScanAll (anon1) > * Once |
| falkordb-capped | point_lookup | True | Results > Project > Node By Index Scan | (movie:Movie) |
| falkordb-capped | filtered_lookup | True | Results > Sort > Project > Node By Index Scan | (movie:Movie) |
| falkordb-capped | hop_3 | True | Results > Sort > Distinct > Project > Conditional Traverse | (peer)->(movie:Movie) > Distinct > Project > Filter > Conditional Traverse | (@anon_0)->(peer:User) > Node By Index Scan | (@anon_0:User) |
| falkordb-capped | aggregation | True | Results > Sort > Aggregate > Conditional Traverse | (@anon_0)-[rating:RATED]->(@anon_1) > All Node Scan | (@anon_0) |
| arangodb-capped | point_lookup | True | SingletonNode > CalculationNode > CalculationNode > FilterNode > CalculationNode > ReturnNode |
| arangodb-capped | filtered_lookup | True | SingletonNode > IndexNode > SortNode > CalculationNode > ReturnNode |
| arangodb-capped | hop_3 | True | SingletonNode > SubqueryStartNode > IndexNode > SubqueryEndNode > SubqueryStartNode > IndexNode > SubqueryEndNode > IndexNode > CalculationNode > CollectNode > SortNode > CalculationNode > ReturnNode |
| arangodb-capped | aggregation | True | SingletonNode > EnumerateCollectionNode > CollectNode > SortNode > CalculationNode > ReturnNode |

## Supporting connection baselines

These client-observed values are not subtracted from workload latency.

| Target | Fresh connect p50/p95 ms | Warm pooled RETURN 1 p50/p95 ms | Failures |
|---|---:|---:|---:|
| cognodb-c0 | 559.218/563.558 | 133.165/137.319 | 0/0 |
| neo4j-aura-free | missing/missing | missing/missing | missing/missing |
| neo4j-ce-capped | 2077.218/2092.899 | 6.326/41.858 | 0/0 |
| memgraph-capped | 2025.514/2057.582 | 2.024/4.938 | 0/0 |
| falkordb-capped | 2041.410/2058.040 | 1.609/4.133 | 0/0 |
| arangodb-capped | 2062.570/2065.740 | 45.635/49.520 | 0/0 |
