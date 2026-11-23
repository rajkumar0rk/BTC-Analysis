# Mean-reversion source and causal-execution gate — 2026-11-24 01:32 IST

## Recovery
Read codex/AGENTS.md, codex/STRATEGY_NOVELTY_GATE.md and family EXPERIMENT_LEDGER.md. Existing successful historical MR004 run 45244913332 at commit 4aceb2c8b168dd625a4682422fb082bd4e66ef9c, branch head 000f5df4dcba696414c9ba4dda198ed25fea1e00. MR004 has only ten trades; not a statistically credible positive mechanism. No new historical run launched here.

## Candidate A — bibshukla/crypto-trading-bot
Source https://github.com/bibshukla/crypto-trading-bot ; pinned commit d2d32e3d4720722794e5769a3799be281c534a86 ; source paths strategy.py, risk_manager.py, tradingview_strategy.pine, README.md. README asserts MIT, but no root LICENSE file was found; rights require confirmation before copying. Original market Coinbase USDC spot multi-asset; Python claims 5m confirmation, Pine defaults 1H ETH/USD. No verified publisher trade count, PF, NAV, drawdown, or complete test period.
Python mean_reversion: long RSI<40 and rising; optional MACD histogram improvement changes confidence, not a mandatory entry; exit RSI>55 or RSI<25 and falling. Position risk: 1.5xATR initial stop capped at 4% distance, 1.5x locked ATR trailing activated after +1%, target config.TAKE_PROFIT_PCT, 5% NAV allocation. Loser strategy is separate: RSI<35 and rising, previous closed-bar volume ratio>=1.5, exit RSI>55 or RSI<25 and falling. Default confidence gate >=0.45 and universe-selection mechanics complicate source-fidelity.
Critical executable discrepancy: tradingview_strategy.pine defaults to combined momentum mode, not mean reversion. Even when switched to 'loser', default RSI momentum gate RSI>45 contradicts loser entry RSI<35; thus ZERO loser entries can satisfy default Pine gates. Pine trend and ADX gates further change the original Python mean-reversion thesis. Do not use Pine reported equity as evidence for the Python model. Python uses current iloc[-1] RSI while volume confidence deliberately uses iloc[-2], requiring explicit completed-bar timing verification.
Novelty: PARTIAL OVERLAP with prior RSI-extreme/Bollinger and MR004 dip research. Incremental hypothesis would be *rising RSI while still oversold with ATR-capped stop*, but source selection, gate contradictions and licensing prevent approval of a source-faithful baseline now. STATUS HOLD; no backtest claimed.

## Candidate B — PatrickSebastine/mean-reversion-trading-bot
Source https://github.com/PatrickSebastine/mean-reversion-trading-bot ; pinned commit c00091d34ad1ee10ede37996883934099bb533c9 ; MIT LICENSE in repository. Original CCXT multi-exchange crypto, mean-reversion entry lower BB touch and RSI<25; upper BB touch and RSI>75 sell signal. Momentum mode is a different family and excluded. Published README has no independently verified Delta BTC 22-month trade ledger, PF, DD, or costs.
Novelty: DUPLICATE of previously audited Patrick Sebastine BB/RSI and MR001 BB/RSI class; source thresholds alone are not novelty. STATUS SKIP. Do not run.

## Candidate C — nickcrane/tradingbot
Source lead https://github.com/nickcrane/tradingbot ; search index describes ETH/GBP RSI+ADX range-only regime and protective stop. GitHub connector GET /repos/nickcrane/tradingbot and /contents both returned 404 on 2026-11-24. No pinned commit/license/executable can be recovered in this session. STATUS NOT REPRODUCIBLE, do not fabricate rules or test.

## Execution/fee gate
Baseline BTC round-trip fee plus GST is (0.0005 * 1.18 * 2) = 0.00118 = 0.118% of constant notional before funding, spread and slippage. This is not a fixed account-NAV debit if risk-based sizing varies. 2026-10 has a known 1,440 UTC-minute data gap. Any new candidate must use next eligible minute open, stop-first and gap-adverse fills, sequential NAV, all IST months, funding UNMODELED and immutable source baseline. No synthetic candles or hindsight filters.

## Session counts and handoff
Three source decisions (one HOLD, one DUPLICATE, one NOT REPRODUCIBLE); zero new distinct historical backtests, zero variants, zero workflow launches. This is a source gate, not a backtest or fix. Next research should seek source-complete, clearly licensed *different* mechanism, preferably established-level liquidity rejection or bounded range oscillation, then commit novelty gate and launch an actual BTC 1m Actions replay. Do not tune MR004's ten-trade sample. No changes to main/master, other families, VPS or trading.
