# Retired legacy strategy families

Removed from main at the maintainer's request to reduce legacy strategy clutter. These are retirement decisions, not claims that every individual variant was unprofitable. Historical source and results are recoverable at [the pre-retirement commit](https://github.com/rajkumar0rk/BTC-Analysis/tree/0ba988119848c6d93a5c1c934795dee3526e5277). The market-data archive, current research branches, locked strategies, Stage24 and current native ETH/BTC dashboard engines are not removed.

## Retired strategy result families

- `analysis/v7_1_2025/`
- `analysis/v7_2_2025/`
- `analysis/v8_1_2025_exits/`
- `analysis/v7_2025/`
- `analysis/v8_2025_behavior/`
- `analysis/big_trend_stage1/`
- `analysis/previous_day_range_swing/`
- `analysis/mtf_swing_range_fixed3r/`
- `analysis/mtf_swing_range_long/`
- `analysis/mtf_swing_range_long_fixed2r/`
- `analysis/mtf_swing_range_short_fixed2r/`
- `analysis/mtf_swing_range_short_fixed3r/`
- `analysis/mtf_uptrend_short_fixed3r/`

## Retired engines

- `scripts/v7_2025_trend_discovery.py`
- `scripts/research_v7_1_retest_2025.py`
- `scripts/research_v7_2_daily_4h_2025.py`
- `scripts/research_v8_2025_big_moves.py`
- `scripts/research_v8_1_2025_exits.py`
- `scripts/research_mtf_swing_range_long.py`
- `scripts/research_mtf_swing_range_long_fixed2r.py`
- `scripts/research_mtf_swing_range_short_fixed2r.py`
- `scripts/research_mtf_swing_range_short_fixed3r.py`
- `scripts/research_mtf_swing_range_fixed3r.py`
- `scripts/research_mtf_uptrend_short_fixed3r.py`
- `scripts/research_big_trend_stage1.py`
- `scripts/research_previous_day_range_swing.py`

## Retired standalone workflows

- `.github/workflows/research-big-trend-stage1.yml`
- `.github/workflows/research-mtf-swing-range-fixed3r.yml`
- `.github/workflows/research-mtf-swing-range-long-fixed2r.yml`
- `.github/workflows/research-mtf-swing-range-long.yml`
- `.github/workflows/research-mtf-swing-range-short-fixed2r.yml`
- `.github/workflows/research-mtf-swing-range-short-fixed3r.yml`
- `.github/workflows/research-mtf-uptrend-short-fixed3r.yml`
- `.github/workflows/research-previous-day-range-swing.yml`
- `.github/workflows/research-v7-1-2025.yml`
- `.github/workflows/research-v7-2-2025.yml`
- `.github/workflows/research-v7-2025.yml`
- `.github/workflows/research-v8-1-2025.yml`
- `.github/workflows/research-v8-2025.yml`

The old ETH replay suite and matching legacy source-result copies are retired. Mixed-suite historical reports remain as recorded evidence; their old filenames do not authorize reruns. ETH all-strategy replay is now manual-only and excludes these engines. Inspect the pre-retirement commit for novelty checks. This commit does not erase Git history, delete other branches, or purge historical Actions artifacts.

## Duplicate branch cleanup
See VERIFIED_DUPLICATE_BRANCHES.json for explicitly reviewed identical branch refs. The pruning workflow deletes only exact SHA duplicates, with open-PR and active-workflow safeguards and an explicit lease. Retained refs keep the same commit. Other research branches are not classified by name alone; review their metrics and active dependencies before retirement.

## Bulk branch consolidation (2026-11-26)

The maintainer approved reducing historical branch refs. The reviewed manifest `RESEARCH_BRANCH_RETIREMENT_20261126.json` records every original head. A separate archive ref preserves each reviewed historical head as an ancestor before lease-protected deletion. Open PRs, active runs, protected refs, changed heads, locked/frozen and retained refs are skipped. Read workflow deletion report for actual outcomes. This is consolidation rather than a claim every retired strategy lost money.
