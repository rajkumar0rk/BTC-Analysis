# Iteration 14 — IST monthly coverage correctness

- Found in `scripts/breakout_range_wavelet_daily_replay.py`: monthly coverage was previously marked `complete` for every month except the first and last *observed* month. Missing UTC 2026-10-31 does not necessarily create a November IST row, so October IST could be mislabeled complete despite missing 18.5 hours or more.
- Minimal repair commit: `92326bf18fef0e96e18f787f6a938c068e717d13`. Count actual observed one-minute IST NAV timestamps per month and compare with exact calendar-month minute count; mark incomplete as `partial_missing_ist_minutes`.
- This is a reporting correction, not a new strategy, and does not alter trading signals, fills, fees or cash accounting.
- Status: **PENDING HISTORICAL VERIFICATION** until the authentic archive workflow completes at this commit, artifact is downloaded, and October month coverage is confirmed partial without changes to prior trade ledgers.
- Prior completed historical control: https://github.com/rajkumar0rk/BTC-Analysis/actions/runs/45110977389 (old commit `a754910`).
- Next action: GET `/repos/rajkumar0rk/BTC-Analysis/actions/runs?branch=research%2Fbreakout-range-source-audit-20261121&per_page=30`, locate SHA `92326bf`, poll jobs to completion, inspect artifacts and compare trade CSVs, summary and monthly NAV. Do not report FIXED_AND_VERIFIED before those checks.
- No new distinct strategy baseline tested; source screens from iteration 13 remain rejected/deferred. Funding and ETH validation remain outstanding.
