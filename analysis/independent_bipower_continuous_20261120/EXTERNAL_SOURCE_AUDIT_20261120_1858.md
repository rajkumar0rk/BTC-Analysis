# External source audit — 2026-11-20 18:58 IST

Prior bipower study is closed REJECTED INACTIVE (BTC zero trades), run 44679516754; do not reopen.

Candidate: https://github.com/aurelien-gentile/turtle-strategy-backtest commit 4a975e6d20a7e6190f350b6443b64631fffcd739 (2026-07-09). Source RULES.md: 20/55-day channel breakout, 10/20-day channel exit, 20-day ATR, initial 2ATR stop, risk 1% of capital, 0.5ATR pyramid steps to four units with halved additions. The repository's top-level listing has no LICENSE file and GitHub repository metadata did not expose a license: code copying NOT authorized; independent rules implementation only after originality and existing Donchian novelty gate review. Need inspect notebook for whether actual implemented rules match reference document; this is NOT an executable audited candidate yet. No BTC screen run launched in this iteration; do not label it screened or profitable.

Required next action: read-only novelty comparison against existing Donchian and Quattro studies, then choose a materially different third-party strategy if overlapping. Build dedicated branch-scoped BTC 2025 zero-slip screen, deduct 0.05% each side + 18% GST, and require genuine Action run and trade artifact. Funding UNMODELED. No main/live changes.
