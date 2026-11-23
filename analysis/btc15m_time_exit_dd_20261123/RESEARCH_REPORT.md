# BTCUSD 15m Reclaim — causal maximum-holding-time research

70 variants x two intra-1m OHLC order assumptions; original engine and 14.74%/+162.964%/18-month benchmark verified each shard.
Only new exit is first 1m open at selected time-limit; stop, target and 8.25% late-protection evaluated normally until then.
Position sizes max 1x, based on number of prior realized losing trades within same IST month; five-loss monthly entry pause on.
Jan2025–Oct2026 repeatedly mined data, in-sample only, no out-of-sample claim. Fees plus GST and 0.02% per-side adverse slippage; funding and real execution unmodeled.

Strict improvements over +162.964% /14.74% /18 months: 0
Improvements over +151.787% /14.74% /18 months: 0; <12% DD qualifying: 0

## Best strict qualifying models
None.

## Best meeting original net and winning months
None.

## Lowest DD irrespective of profit
| tier      |   timeout_hours |   max_floating_dd |   min_net |   min_profitable_months |   min_trades |   max_trades |   max_fee_gst | qualify_current   | qualify_original   | target12   |
|:----------|----------------:|------------------:|----------:|------------------------:|-------------:|-------------:|--------------:|:------------------|:-------------------|:-----------|
| T65_20_10 |              24 |            14.116 |   38.4517 |                      12 |          212 |          212 |      191.299  | False             | False              | False      |
| T65_30_10 |              24 |            14.183 |   38.7264 |                      13 |          212 |          212 |      197.38   | False             | False              | False      |
| T75_10_10 |              24 |            14.35  |   39.2444 |                      12 |          212 |          212 |      192.171  | False             | False              | False      |
| T85_10_10 |              24 |            14.653 |   40.3056 |                      12 |          212 |          212 |      199.113  | False             | False              | False      |
| T85_20_10 |              24 |            14.719 |   40.6025 |                      12 |          212 |          212 |      205.194  | False             | False              | False      |
| T65_30_10 |               0 |            14.74  |  162.964  |                      18 |           72 |           72 |       93.3781 | False             | False              | False      |
| T65_30_10 |            1440 |            14.74  |  162.964  |                      18 |           72 |           72 |       93.3781 | False             | False              | False      |
| T65_30_10 |             960 |            14.74  |  141.489  |                      17 |           73 |           73 |       95.1247 | False             | False              | False      |
| T65_20_10 |               0 |            15.068 |  165.689  |                      18 |           72 |           72 |       92.82   | False             | False              | False      |
| T65_20_10 |            1440 |            15.068 |  165.689  |                      18 |           72 |           72 |       92.82   | False             | False              | False      |
| T65_20_10 |             960 |            15.068 |  143.991  |                      17 |           73 |           73 |       94.5847 | False             | False              | False      |
| T75_10_10 |               0 |            16.081 |  174.105  |                      18 |           72 |           72 |       96.1425 | False             | False              | False      |
| T75_10_10 |            1440 |            16.081 |  174.105  |                      18 |           72 |           72 |       96.1425 | False             | False              | False      |
| T75_10_10 |             960 |            16.081 |  151.72   |                      17 |           73 |           73 |       97.9631 | False             | False              | False      |
| T85_20_10 |               0 |            16.152 |  176.951  |                      18 |           72 |           72 |      100.666  | False             | False              | False      |
| T85_20_10 |            1440 |            16.152 |  176.951  |                      18 |           72 |           72 |      100.666  | False             | False              | False      |
| T85_20_10 |             960 |            16.152 |  154.334  |                      17 |           73 |           73 |      102.505  | False             | False              | False      |
| T85_10_10 |               0 |            16.62  |  179.783  |                      18 |           72 |           72 |      100.099  | False             | False              | False      |
| T85_10_10 |            1440 |            16.62  |  179.783  |                      18 |           72 |           72 |      100.099  | False             | False              | False      |
| T85_10_10 |             960 |            16.62  |  156.935  |                      17 |           73 |           73 |      101.958  | False             | False              | False      |
| T65_30_10 |             720 |            17.162 |  110.203  |                      16 |           76 |           76 |       91.8739 | False             | False              | False      |
| T65_30_10 |              48 |            17.38  |   29.8815 |                      11 |          178 |          178 |      165.491  | False             | False              | False      |
| T65_20_10 |             720 |            18.07  |  108.73   |                      16 |           76 |           76 |       90.1149 | False             | False              | False      |
| T65_20_10 |              12 |            18.19  |   -8.4397 |                       6 |          205 |          205 |      131.406  | False             | False              | False      |
| T65_20_10 |              48 |            18.214 |   29.7692 |                      11 |          178 |          178 |      160.616  | False             | False              | False      |

## Important
All reported DD is maximum open-position inclusive floating drawdown. Test assumptions are theoretical OHLC paths, not tick-level order book fills. Reducing hold time can lower DD while losing large trends, so preserve profit and month conditions.
