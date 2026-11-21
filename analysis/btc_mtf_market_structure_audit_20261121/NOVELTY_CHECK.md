# BTC 1H+4H multi-regime market-state audit (2026-11-21)

Decision: PARTIAL OVERLAP — approved DIFFERENTIAL classification-quality research, NOT alpha optimization.

Previous work reviewed:
- scripts/research_btc_regime_attribution_20261121.py and analysis/btc_regime_attribution_20261121/: eight 1H states, mostly MIXED; four losing strategy baselines. Did not audit multi-timeframe current-trend confirmation.
- scripts/research_btc_multiregime_audit_20261121.py and analysis/btc_multiregime_audit_20261121/: original 1H labels had 27.34% hourly switching and no historical revisions.
- scripts/research_btc_selector_hardening_20261121.py: fixed selector lost 34.86%, strict past-only selector stayed out of market.
- scripts/research_btc_directional_diagnosis_20261121.py, research/btc-path-aware-direction-20261121: future directional and profitable-outcome models failed. These are NOT tests of whether current chart trend is observable.
- analysis/institutional_discovery_stage13_4h_1h_15m/, research/stage24-monthly10, research/stage25-new-trend: multi-timeframe entry families tested; this study claims no novel EMA/ADX alpha.
- codex/STRATEGY_NOVELTY_GATE.md: gate.

Differential question: Is an independently computed current 1H+4H trend state causal and structurally consistent, vs incorrectly equating trend labels with next4H UP/DOWN outcomes? This audit introduces NO trades or parameter search.

Frozen rules: native 1M BTCUSD SHA verified, 992160 minutes 2025-01-01 through 2026-11-20; 60 complete minutes per 1H, 240 per 4H. Compute UTC aligned 1H and 4H and allow a 4H aggregate only when the entire 4H candle has closed by the current 1H close (strict backward asof). Never use incomplete 4H or future price in states. Require complete warmup before classifying.

1H up candidate: EMA20>EMA50, close>EMA20, ADX14>=20, positive DMI dominance, EMA20 slope(4 1H)>0, efficiency12>=0.22; down exact symmetry.
4H up candidate: EMA20>EMA50, close>EMA20, ADX14>=20, positive DMI dominance, EMA20 slope(2 4H)>0, efficiency6>=0.20; down symmetric.
States in priority: SHOCK (1H true range >2.2 ATR14 or ATR/previous72h median>=1.8), CONFIRMED_TREND_UP/DOWN (aligned 1H/4H), BREAKOUT_UP/DOWN (close outside preceding 24 complete 1H channel and not confirmed), TRANSITION (explicit 1H/4H opposing candidate direction), COMPRESSION (ATR ratio<=0.75, ER12<=0.22, ADX<=24), RANGE (ADX<=19, ER12<=0.35, 4H EMA20/50 gap <=1.2 ATR4H), otherwise MIXED_UNCERTAIN. Warmup is UNCLASSIFIED, not MIXED. No future information, mutually exclusive label.

Tests: 3 truncated-history replays to verify old labels invariant; complete hourly and four-hour spans; exact 4H availability timestamps; state counts for each 22 complete IST month; percent mixed and state changes, median runs, independent trailing 24H directional price-structure alignment (NOT objective regime truth), and NEXT 4H and 12H nonoverlapping direction followthrough purely as diagnostic, split 2025/2026. No optimizing parameters based on output.

Deliver scripts, quality audit, report and CSV with all individual 1H states; no live trade approval or profitability claims. 2025-2026 not untouched holdout and no 22/22 profit demonstrated.
