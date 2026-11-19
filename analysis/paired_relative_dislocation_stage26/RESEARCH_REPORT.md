# Stage26 cross-asset relative BTC/ETH dislocation and reversion

Both native perpetual instruments use identical dimensionless rules, symmetric relative directions.

2025 shared monthly selection applied unchanged in 2026; no live validation.

## 2025-only candidate ranking

|   z_threshold |   min_reversion |   atr_stop |   reward_R |   jointly_pf1p5_and_5pct |   strong_pf_months |   positive_months |   median_month_return |   trades_2025 |   drawdown |
|--------------:|----------------:|-----------:|-----------:|-------------------------:|-------------------:|------------------:|----------------------:|--------------:|-----------:|
|           1.8 |            0.15 |        1.5 |          2 |                        0 |                  6 |                10 |             -0.123248 |            99 |    8.21129 |
|           1.8 |            0.15 |        1.5 |          3 |                        0 |                  6 |                10 |             -0.123248 |            96 |    8.07227 |
|           1.2 |            0.15 |        1.5 |          3 |                        0 |                  5 |                10 |             -0.157404 |           155 |   12.3891  |
|           1.2 |            0.15 |        2.5 |          2 |                        0 |                  5 |                10 |             -0.253304 |           139 |    9.26965 |
|           1.8 |            0.15 |        2.5 |          2 |                        0 |                  5 |                 9 |             -0.270759 |            83 |    5.99905 |
|           1.2 |            0.15 |        2.5 |          3 |                        0 |                  5 |                 8 |             -0.272204 |           134 |    8.61491 |
|           1.2 |            0.15 |        1.5 |          2 |                        0 |                  4 |                11 |             -0.348439 |           155 |   13.7024  |
|           1.2 |            0.35 |        1.5 |          2 |                        0 |                  4 |                 9 |             -0.255124 |            76 |   13.2972  |
|           1.2 |            0.35 |        1.5 |          3 |                        0 |                  4 |                 9 |             -0.403758 |            77 |   13.044   |
|           1.2 |            0.35 |        2.5 |          2 |                        0 |                  4 |                 8 |             -0.173729 |            66 |    9.17912 |
|           1.8 |            0.35 |        1.5 |          2 |                        0 |                  3 |                 9 |             -0.307426 |            52 |    7.3683  |
|           1.2 |            0.35 |        2.5 |          3 |                        0 |                  3 |                 8 |             -0.173729 |            65 |    8.3478  |

## Selected BTC vs ETH 22 IST calendar months

| month_ist   | symbol   |   net_return_pct |   profit_factor |   trades |   wins |   losses |
|:------------|:---------|-----------------:|----------------:|---------:|-------:|---------:|
| 2025-01     | BTCUSD   |        0         |     nan         |        0 |      0 |        0 |
| 2025-01     | ETHUSD   |        0         |     nan         |        0 |      0 |        0 |
| 2025-02     | BTCUSD   |       -1.55062   |       0.280329  |        6 |      1 |        5 |
| 2025-02     | ETHUSD   |        0.669069  |       2.08685   |        4 |      2 |        2 |
| 2025-03     | BTCUSD   |       -1.34514   |       0.352166  |        6 |      2 |        4 |
| 2025-03     | ETHUSD   |       -0.246496  |       0.61918   |        6 |      4 |        2 |
| 2025-04     | BTCUSD   |       -0.886135  |       0.186151  |        4 |      1 |        3 |
| 2025-04     | ETHUSD   |        0.474825  |       1.44798   |        6 |      3 |        3 |
| 2025-05     | BTCUSD   |       -0.545755  |       0.491925  |        4 |      2 |        2 |
| 2025-05     | ETHUSD   |        0.0159673 |       1.01033   |        6 |      3 |        3 |
| 2025-06     | BTCUSD   |       -1.1686    |       0.450106  |        5 |      1 |        4 |
| 2025-06     | ETHUSD   |        1.43944   |       3.73914   |        3 |      2 |        1 |
| 2025-07     | BTCUSD   |        1.18211   |       3.09034   |        5 |      4 |        1 |
| 2025-07     | ETHUSD   |       -1.92407   |       0.0755981 |        6 |      2 |        4 |
| 2025-08     | BTCUSD   |        0.963357  |       1.80674   |        6 |      3 |        3 |
| 2025-08     | ETHUSD   |       -1.23449   |       0.525873  |        8 |      3 |        5 |
| 2025-09     | BTCUSD   |        0.0708744 |       1.12661   |        2 |      1 |        1 |
| 2025-09     | ETHUSD   |       -0.939477  |       0.112354  |        3 |      1 |        2 |
| 2025-10     | BTCUSD   |       -0.516252  |       0         |        1 |      0 |        1 |
| 2025-10     | ETHUSD   |        0.985825  |     inf         |        1 |      1 |        0 |
| 2025-11     | BTCUSD   |        1.04479   |       8.77777   |        3 |      2 |        1 |
| 2025-11     | ETHUSD   |       -0.528734  |       0.659537  |        5 |      2 |        3 |
| 2025-12     | BTCUSD   |       -1.17709   |       0.250524  |        5 |      2 |        3 |
| 2025-12     | ETHUSD   |        0.680141  |       1.64682   |        4 |      2 |        2 |
| 2026-01     | BTCUSD   |        0.112715  |       1.06265   |        6 |      2 |        4 |
| 2026-01     | ETHUSD   |       -0.206785  |       0.902321  |        6 |      2 |        4 |
| 2026-02     | BTCUSD   |        1.42561   |       3.60774   |        4 |      2 |        2 |
| 2026-02     | ETHUSD   |       -1.57722   |       0.37718   |        6 |      1 |        5 |
| 2026-03     | BTCUSD   |       -0.936694  |       0.114437  |        3 |      1 |        2 |
| 2026-03     | ETHUSD   |        1.02138   |     inf         |        2 |      2 |        0 |
| 2026-04     | BTCUSD   |       -0.49325   |       0.310972  |        4 |      2 |        2 |
| 2026-04     | ETHUSD   |       -0.137252  |       0.741955  |        4 |      3 |        1 |
| 2026-05     | BTCUSD   |       -0.0206999 |       0.940865  |        3 |      1 |        2 |
| 2026-05     | ETHUSD   |       -1.60321   |       0         |        3 |      0 |        3 |
| 2026-06     | BTCUSD   |       -0.194449  |       0         |        2 |      0 |        2 |
| 2026-06     | ETHUSD   |       -0.0158491 |       0.969241  |        2 |      1 |        1 |
| 2026-07     | BTCUSD   |       -0.631127  |       0.435416  |        3 |      1 |        2 |
| 2026-07     | ETHUSD   |       -0.138591  |       0.872173  |        4 |      1 |        3 |
| 2026-08     | BTCUSD   |        2.41164   |       5.50778   |        4 |      3 |        1 |
| 2026-08     | ETHUSD   |       -0.679658  |       0.347818  |        3 |      1 |        2 |
| 2026-09     | BTCUSD   |        0.926604  |      30.499     |        2 |      1 |        1 |
| 2026-09     | ETHUSD   |       -0.342937  |       0.362963  |        2 |      1 |        1 |
| 2026-10     | BTCUSD   |        1.7575    |       2.61937   |        5 |      3 |        2 |
| 2026-10     | ETHUSD   |       -1.83539   |       0.158326  |        5 |      1 |        4 |

## 2025 full calendar year vs 2026 Jan-Oct YTD

| symbol   |   z_threshold |   min_reversion |   atr_stop |   reward_R | stress   |   trades |   wins |   losses |   PF_overall |   PF_2025 |   PF_2026YTD |   strong_months |   strong_positive_months |   strong_5pct_months |   months_positive |   months_negative |   months_ge5pct |   months_ge10pct |   months_ge20pct |   median_month_return_pct |   median_finite_PF_3trades |   worst_month_pct |   net_return_2025_FULL_YEAR_pct |   net_return_2026_JanOct_YTD_pct |   net_return_22months_pct |   max_drawdown_pct | over_500pct_2025_full_year   |
|:---------|--------------:|----------------:|-----------:|-----------:|:---------|---------:|-------:|---------:|-------------:|----------:|-------------:|----------------:|-------------------------:|---------------------:|------------------:|------------------:|----------------:|-----------------:|-----------------:|--------------------------:|---------------------------:|------------------:|--------------------------------:|---------------------------------:|--------------------------:|-------------------:|:-----------------------------|
| BTCUSD   |           1.8 |            0.15 |        1.5 |          2 | False    |       83 |     35 |       48 |     1.01533  |  0.692214 |     1.58639  |               6 |                        6 |                    0 |                 9 |                12 |               0 |                0 |                0 |                 -0.107574 |                   0.491925 |          -1.55062 |                       -3.90893  |                          4.38516 |                 0.304825  |            5.59678 | False                        |
| BTCUSD   |           1.8 |            0.15 |        1.5 |          2 | True     |       83 |     35 |       48 |     1.00344  |  0.685246 |     1.564    |               6 |                        6 |                    0 |                 9 |                12 |               0 |                0 |                0 |                 -0.115716 |                   0.485245 |          -1.56314 |                       -4.01562  |                          4.25536 |                 0.0688614 |            5.65047 | False                        |
| ETHUSD   |           1.8 |            0.15 |        1.5 |          2 | False    |       89 |     38 |       51 |     0.755254 |  0.948477 |     0.547123 |               3 |                        3 |                    0 |                 7 |                14 |               0 |                0 |                0 |                 -0.172688 |                   0.659537 |          -1.92407 |                       -0.659147 |                         -5.41451 |                -6.03797   |            8.21129 | False                        |
| ETHUSD   |           1.8 |            0.15 |        1.5 |          2 | True     |       89 |     38 |       51 |     0.742025 |  0.933612 |     0.535765 |               3 |                        3 |                    0 |                 6 |                15 |               0 |                0 |                0 |                 -0.203324 |                   0.650529 |          -1.95186 |                       -0.855636 |                         -5.60557 |                -6.41324   |            8.50737 | False                        |

## Assumptions and exclusions

{
  "rule": "4h log BTC/ETH price ratio z-score vs previous 120 completed 4h bars; enter relative mean reversion after initial inward z-score movement",
  "causality": "Completed 4h right-edge signals, execution on next 1m open; no future values in history",
  "independent_models_each_market": 16,
  "candidate_events": 1974,
  "shared_2025_selection_only": true,
  "sources": {
    "BTCUSD": {
      "symbol": "BTCUSD",
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-10-31 18:29:00+00:00",
      "partition_SHA256": {
        "2025-01.csv.gz": "5d0ebde1cc87acf5a099972ab26cd9e9e26d5964a2bc1b2a8e1fa17ca234bba0",
        "2025-02.csv.gz": "0f50eed68eca54582d29104a32af94b66a0be4102ee7dd664dd139618303238d",
        "2025-03.csv.gz": "04aca2d3944bbcc507f26d301d4ccee0dff06a8e8c56f929b4b31a5941ebaa69",
        "2025-04.csv.gz": "5bd04594456dbde7943310201078cbf3169a9cb8a7cb6989d2f81b3ef6793b38",
        "2025-05.csv.gz": "c9c670972b786ba16d6b8d8eb0acf15e6b1a517370b7ab090e1c0cc71b65df51",
        "2025-06.csv.gz": "93956a2f915be5467f5dda779cd07b00d8f119db0d4b05b54000d52691cc8e78",
        "2025-07.csv.gz": "11e969bb74b8f53c9ba208eb41e17b1ff4173a3bf2d5840dbe870f879e429c17",
        "2025-08.csv.gz": "f5282ce351d5afab93b2397083e2aebe429dc80757deb2a03af8998f60e78db5",
        "2025-09.csv.gz": "bbf4ad093093546242c69509fd6724cba2cdfa8636c7d3d191e2a313395cd2c9",
        "2025-10.csv.gz": "641a837a6ee6ca45c57e2f00aeb645e98dfd4adee3361cf305a1d1198539285e",
        "2025-11.csv.gz": "29ad16d3c65e386c23cdd523ae4fdc1c4f07f1db1a782b07c2d904e5f4e4a067",
        "2025-12.csv.gz": "adc35407d4648dfc4a1bb64d1393a0fc69d2aa43914cce38e1ae8636f7b53f18",
        "2026-01.csv.gz": "81bfe747c61384e1819889d7728bd1565adf2f37370320cb9b541e59259e5f6f",
        "2026-02.csv.gz": "9f65468800bd92893d7aff4e1e6eb4079c8c9f92c5fc2166afe7b13817e3d2d0",
        "2026-03.csv.gz": "2092dbd9ff56827ec98e52312d744b4a24b30e995323478d05ab0aed86392a51",
        "2026-04.csv.gz": "ac949c3669ebe2e47eb2e59c98df6da60727a9fdf54274fd9df3a376c844ce36",
        "2026-05.csv.gz": "6b66e854500a0edefebf0edb0c24cd218f4de009482e09980fe9041418a3dea8",
        "2026-06.csv.gz": "b4e588d4ace8df0ca7a01d92ad2ccf39eba5a624d4c7eba3e658d330b90838e1",
        "2026-07.csv.gz": "a41cf0ce175302dcf8da1ed629efb01fc9cbbbf83d2d8e4369cd3b1a9e7d8bd0",
        "2026-08.csv.gz": "487592c47d21ff540ba574c11487eb7c1a62e7d498c930fe86e9efd19e9338e0",
        "2026-09.csv.gz": "8625a04c80c029ef31abf39c66b0bdf58de38c06228178c5472a203301d071cb",
        "2026-10.csv.gz": "118135c40c1ef97a325c85a6aace8ebe45de88cb723a4da624b4a4f5b31043e6",
        "2026-11.csv.gz": "68cd70174cbfdb67433fa0d6886b8e03be85902dda3963cc8fdfb1e671802fa5"
      },
      "IST_months": {
        "2025-01": {
          "observed": 44310,
          "expected": 44640,
          "missing": 330
        },
        "2025-02": {
          "observed": 40320,
          "expected": 40320,
          "missing": 0
        },
        "2025-03": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-04": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-05": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-06": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-07": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-08": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-09": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-10": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-11": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-12": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-01": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-02": {
          "observed": 40320,
          "expected": 40320,
          "missing": 0
        },
        "2026-03": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-04": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-05": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-06": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-07": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-08": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-09": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-10": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        }
      },
      "initial_2025_IST_gap_minutes": 330,
      "October_2026_UTC_archive_complete": true
    },
    "ETHUSD": {
      "symbol": "ETHUSD",
      "first_utc": "2025-01-01 00:00:00+00:00",
      "last_utc": "2026-10-31 18:29:00+00:00",
      "partition_SHA256": {
        "2025-01.csv.gz": "ec8b73a45e93258f11850cbb7b07913e26f1fdb623d7f9c18bbc637e219270cc",
        "2025-02.csv.gz": "065233cc53e2ee19ce2c3f41c57e22d3b2dee9f91458b83b2072f4facadd4e1d",
        "2025-03.csv.gz": "0d13ec3a042b2d2ce89763003876311f8f96bba1609f3edb6ff2b5480752f852",
        "2025-04.csv.gz": "56bafdbbfd1968c15a3bd92157150141d3c97e13cf133541d6474106e308d9de",
        "2025-05.csv.gz": "6034f38fa7ec4cc319af69bc9905cbb87a9aab796069d0a7d8c9cb8ae0cac855",
        "2025-06.csv.gz": "6121275461d16465dd377c2337752e24bc4ca43190695ebda76c210e6c4907de",
        "2025-07.csv.gz": "259616aad32315dce665ca47c0101c9e18b32352171c1a431de7ac31333dba8e",
        "2025-08.csv.gz": "7f3605addb5e9d9c470d36d1f1adb42f6641f1b4ee1e94c60b63504837c264af",
        "2025-09.csv.gz": "2bc385d896a639e4c45cf827bc6d8c8250bb0e77132bb3607ce8b04bc74d95ca",
        "2025-10.csv.gz": "c9484143d69ce7bed794741753b5de56dca0415d842371e1c6f9068bb7b3ef18",
        "2025-11.csv.gz": "e81025b5550c496463617158b046bb8a91d30cb3277614964eee844b5ab1c770",
        "2025-12.csv.gz": "239546a1b57d78c4f6f046a7e425d38a7ea648e5a4923b0038ef639d10b713ef",
        "2026-01.csv.gz": "949d680d39c19f554ab0d0eee5c90bd7b7e632051897651c8c7800db775e7a79",
        "2026-02.csv.gz": "56734d2cbe9847e01d6441cb8e6a1d9266caa29849d96afe4a76bf46c461364b",
        "2026-03.csv.gz": "1ede5a30ee76b051670c8e379dad6b409758ba7c4121bd066a6f70247ee145fd",
        "2026-04.csv.gz": "fd1f0e4f5352bd55945c326e76d06692fc1f3e933e8e5ac85f769ac905df251c",
        "2026-05.csv.gz": "e3ebe5d1731e84481692cbba5c10aaffc85a1b4cec9142bd9fcd498bd32151f9",
        "2026-06.csv.gz": "40de88ecaa0125db6046d9306ecb4dbe8cdcb28993ae7adc49ee707ccc88b1db",
        "2026-07.csv.gz": "fc47057f758b28b47062b162fe847825b9e1eb8219763f20372bcf5443076004",
        "2026-08.csv.gz": "5e189c23f0ec164da952acc47189cd2d87491517e1128f7b3a0913ae087e84f0",
        "2026-09.csv.gz": "610cad705b83daf22756fe4b7408078f0aadbcd24239bc6f0c46751b093198f4",
        "2026-10.csv.gz": "246e8e1cbdae00a9832a69be3cc2a399fff764dec6822edbe867efae84db0d2b",
        "2026-11.csv.gz": "2fa13ebf9d3219a5305f15ad982714c3ae3c2f96ae665ddd01157812dda05cf2"
      },
      "IST_months": {
        "2025-01": {
          "observed": 44310,
          "expected": 44640,
          "missing": 330
        },
        "2025-02": {
          "observed": 40320,
          "expected": 40320,
          "missing": 0
        },
        "2025-03": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-04": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-05": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-06": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-07": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-08": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-09": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-10": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2025-11": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2025-12": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-01": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-02": {
          "observed": 40320,
          "expected": 40320,
          "missing": 0
        },
        "2026-03": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-04": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-05": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-06": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-07": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-08": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        },
        "2026-09": {
          "observed": 43200,
          "expected": 43200,
          "missing": 0
        },
        "2026-10": {
          "observed": 44640,
          "expected": 44640,
          "missing": 0
        }
      },
      "initial_2025_IST_gap_minutes": 330,
      "October_2026_UTC_archive_complete": true
    }
  },
  "fees": {
    "taker_side": 0.0005,
    "GST": 0.18,
    "BTC_slip_per_side": 5,
    "BTC_stress": 10,
    "ETH_slip_fraction_per_side": 0.0002,
    "ETH_stress": 0.00035
  },
  "risk": {
    "initial_usd": 10000.0,
    "trade_risk": 0.005,
    "max_leverage": 3.0,
    "max_hold_minutes": 2880
  },
  "limitations": [
    "2025 January missing first 330 IST minutes",
    "Funding settlement cashflow not reconstructed",
    "Actual historical bid-ask, L2 depth and price impact not verified",
    "Contract lot sizes, maintenance margin and liquidation not verified",
    "Contrarian side on BTC vs ETH does not guarantee synchronized market-neutral hedge",
    "Same 1m bar stop/target ambiguous => stop wins; gap stop adverse",
    "2026 previously seen, not a pristine forward holdout"
  ]
}
