# Stage 25 — Independently optimize five negative BTCUSD sleeves (research only)

**Commit/run:** GitHub Actions run [44900321520](https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/44900321520), succeeded 2026-11-21.

## Scope and source

Recomputed entries and exits from 989,280 Delta India BTCUSD **1-minute** candles in 23 monthly source partitions (January 2025 through the currently recorded November 2026 window). The comparison is strictly **January 2025 through October 2026 (22 months)**. Replayed **1,640** fixed strategy variants across the five original losing sleeves.

Sources are the original Stage17 Donchian swing, Stage19 1-hour signal families, Stage20 5-minute compression pattern. Entries at **next 1-minute open after completed higher-timeframe signal**. Stops win same-minute stop/target ties. Default costs **0.05% taker fee each leg + GST 18% on fees + 5 BTC quote points adverse slippage per leg**. Nominal account sizing uses 0.5% initial-risk per trade, leverage cap 5x for 1H/5M. The 4H swing uses the original Stage17 0.5% risk sizing and monthly mark-to-market. No funding, actual spread, liquidation, contract sizing or shared account model.

**Selection:** One variant per original sleeve based only on 2025 training-period return/drawdown/month wins (with an approximate extra 2 bps/leg for the intraday models). All 2026 results are **previously researched**, so they cannot be called pristine out-of-sample results. Original baseline models are preserved unchanged.

## Results — all returns are independent, not allocated portfolio

| Previously negative original | Original on CURRENT 1m | 2025-selected version | 2025 | Jan–Oct 2026 | 22 months | Profitable / losing / flat months |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| 4H Donchian55 EMA50 3×ATR trail | −5.19% | **4H Donchian24, EMA50 filter, trail 2.5×ATR** | +1.85% | +7.12% | **+9.11%** | 9 / 13 / 0 |
| 1H compression, H4 efficiency≥30%, 2R, 4h | −0.06% | 1H compression, **unfiltered short**, 2.5R, max 8h | +0.002% | +1.41% | **+1.41%** | 8 / 7 / 7 |
| 1H compression unfiltered, 3R, 4h | −0.14% | **Same** 1H compression unfiltered short, 2.5R, 8h | +0.002% | +1.41% | **+1.41%** | 8 / 7 / 7 |
| 1H EMA20 pullback, efficiency≥30%, 3R, 4h | −12.32% | **1H EMA20 pullback, LONG only, 5R, max 8h** | +4.90% | +2.64% | **+7.66%** | 12 / 10 / 0 |
| 5M compression, large ATR, 4R, 2h | −13.62% | 5M compression REVERSE, large ATR, structural stop, 2R, max 4h | −0.97% | −5.67% | **−6.58%** | 9 / 13 / 0 |

*Compression selections are duplicates from two original negative sleeves; they are **ONE independent traded strategy**, not two diversified sources.*

### Costs and robustness

| Candidate | Base extra cost | Additional 2 bps per side (approx) | Additional 5 bps per side (approx) |
| --- | ---: | ---: | ---: |
| 4H Donchian24 EMA50 trail2.5 | +9.11% | Not computed — monthly MTM | Not computed — monthly MTM |
| 1H compression short, 2.5R, max 8h | +1.41% | +0.78% | **−0.17%** |
| 1H EMA20 LONG, 5R, max 8h | +7.66% | +4.10% | **−1.03%** |
| 5M compression reverse/structural/2R | **−6.58%** | **−10.49%** | **−16.05%** |

Extra-cost scenarios use a conservative surcharge on both legs, **approximated using entry quote notional**, in addition to standard 0.05% taker plus GST + 5-pt/side slippage. This is not a fully integrated execution or order-book stress simulation.

## Decision

- **Research candidate:** 4H Donchian24 EMA50 + 2.5×ATR trail. Positive 2025 and 2026, +9.11% overall; *only 9 of 22 months positive* and extra-cost sensitivity untested.
- **Research candidate:** 1H EMA20 pullback, LONG only, 5R, 8h max hold. Positive in both years, +7.66% overall; net return becomes negative with the +5-bps/side surcharge.
- **Weak / monitor only:** The short compression variant gives barely above 0% during 2025; 28 total trades, and becomes negative with +5bps/side. Do not count two duplicate selections as diversification.
- **Reject:** All 720 M5 compression variants tested failed to produce a positive 22-month result, even if choosing the best with full-history hindsight (best −3.66%). The 2025-selected variant remains −6.58%.

## Quality

1. Original outcomes closely reproduced with current source. **Current BTC 1m archive has no missing candles**; the original historical files used in prior research had a missing source day in late October 2026. Consequently, updated 22-month original returns differ by −0.08 percentage points for 4H Donchian55 and −0.32 percentage points for 1H EMA pullback. Both 2025 training returns matched their archived references.
2. The 1H/5M analysis books trades at **exit month**, unlike the swing that marks positions to market at IST month end; therefore comparing monthly consistency across families requires care.
3. All candidates are research exposed; none justifies real-money trading without a new forward test, portfolio-level margin controls and independent execution audit.
4. There are no side effects on existing active strategies, no merge to \`main\`, no VPS deployment, no real-money orders.

## Reproduction and machine-readable reports

\`\`\`bash
PYTHONPATH=scripts python scripts/research_stage25_optimize_five_negative_sleeves_20261121.py
\`\`\`

Retrieve GitHub Actions artifact **btc-stage25-all-five-standalone-optimization** from run 44900321520. It contains \`all_five_families_trade_replay_summary.csv\`, \`baseline_vs_train_selected_vs_invalid_hindsight.csv\`, \`baseline_and_selected_monthly.csv\`, \`all_candidate_monthly_results.csv.gz\`, and \`quality.json\`.
