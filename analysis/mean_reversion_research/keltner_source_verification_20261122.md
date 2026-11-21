# KeltnerBounceV1 frozen-source verification — 2026-11-22

Status: NOT APPROVED; NO BTC BACKTEST; source verification only.

Source: https://github.com/IvPalmer/Master-Trader/blob/912d9ff1cb0e638e52131950d2d82a56f2ad428e/ft_userdata/user_data/strategies/KeltnerBounceV1.py

Verified directly against upstream pinned revision: 1h long-only close crossback above SMA25(close) minus 2.5 * SMA25(true range); volume >1.75 * SMA20(volume); BTC/USDT 1h close above its SMA50; startup 200 1h candles; -7% stop; trailing positive 3% after +5% offset; ROI +10% initially, +7% after 360 minutes, +4% after 720, +2% after 1440. No explicit exit signal. The ATR helper is SIMPLE moving average of true range, not Wilder smoothing. The code is a Freqtrade spot strategy for altcoin pairs and does not supply a BTC futures baseline. BTC used as a market gate for altcoins becomes a same-instrument gate on BTCUSD, changing the research question. Publisher claims cannot be transferred to BTC.

Source license: no root LICENSE at the pinned revision; permission for source-code reuse remains unverified. Do not copy upstream code. The prior audit `source_discovery_20261122_keltnerbounce.md` documents the publisher's selection and results.

Required next decision: inspect Stage19/23/24 entry/exit mechanisms on their actual branches and record the exact closest matches in a committed NOVELTY_CHECK.md. If the channel crossback is merely a parameterized envelope/RSI reversal, mark SKIP; otherwise approve a distinct hypothesis with the BTC self-gate difference and launch a source-faithful replay using original 1h signals and next 1m open. Do not run before gate approval. Funding and gaps must be disclosed. No claims of local BTC profitability.
