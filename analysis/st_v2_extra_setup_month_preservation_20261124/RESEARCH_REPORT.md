# V2 independent extra setup: historical no-harm screening

Original 108 trades: 67 Line Touch LONG, 18 Bullish Flip LONG, 23 Bearish Flip SHORT. Baseline 18/22, +22633.90 points, closed drawdown 2642.53.
Single position and signed ST cycle cap. New entries compete chronologically; a candidate that blocks any original trade fails. No future core-trade reservation. 1m stop-first. Same estimated costs. Deduplicated entry masks, four setup families.

## Strict candidates
| config                                     |   core_trades_kept |   extra_trades |   positive_months |   net_2025 |   net_2026 |   net_points |   max_dd |   any_month_degraded |
|:-------------------------------------------|-------------------:|---------------:|------------------:|-----------:|-----------:|-------------:|---------:|---------------------:|
| confirm|short|le1.0|atr0.4|off|sl1.0|tp1.5 |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.5|tp1.5 |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.0|tp1.5  |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.5|tp1.5  |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.75|tp1.5  |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl1.0|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl1.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl0.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl0.75|tp1.5  |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl1.0|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl1.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl0.75|tp1.5  |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl1.0|tp1.5   |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl1.5|tp1.5   |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.0|tp1.0 |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.5|tp1.0 |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.0|tp1.0  |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.5|tp1.0  |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.5|tp1.0   |                108 |              1 |                18 |    17676.8 |    5910.76 |      23587.6 |  2642.53 |                    0 |

## Strict ALL months nondecreasing
| config                                     |   core_trades_kept |   extra_trades |   positive_months |   net_2025 |   net_2026 |   net_points |   max_dd |   any_month_degraded |
|:-------------------------------------------|-------------------:|---------------:|------------------:|-----------:|-----------:|-------------:|---------:|---------------------:|
| confirm|short|le1.0|atr0.4|off|sl1.0|tp1.5 |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.5|tp1.5 |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.0|tp1.5  |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.5|tp1.5  |                108 |              2 |                18 |    16723.1 |    7722.45 |      24445.6 |  2392.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.75|tp1.5  |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl1.0|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl1.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl0.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl0.75|tp1.5  |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl1.0|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le0.8|atr0.3|H4|sl1.5|tp1.5   |                108 |              1 |                18 |    18220.3 |    5910.76 |      24131.1 |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl0.75|tp1.5  |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl1.0|tp1.5   |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|long|le1.0|atr0.4|H1|sl1.5|tp1.5   |                108 |              1 |                18 |    17926.2 |    5910.76 |      23837   |  2642.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.0|tp1.0 |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|off|sl1.5|tp1.0 |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.0|tp1.0  |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|short|le1.0|atr0.4|H1|sl1.5|tp1.0  |                108 |              2 |                18 |    16723.1 |    7063.4  |      23786.5 |  2392.53 |                    0 |
| confirm|long|le0.8|atr0.2|H4|sl0.5|tp1.0   |                108 |              1 |                18 |    17676.8 |    5910.76 |      23587.6 |  2642.53 |                    0 |

## Caveats
All periods previously seen. Multiple comparisons, not independent forward evidence. No funding, liquidation, margin or order-book effects.
