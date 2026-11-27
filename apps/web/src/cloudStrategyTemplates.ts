/** Exact reviewed SDK wrappers. No uploaded source execution. */
export const mtfPullbackTemplates=[
  {
    "mode": "touch",
    "name": "MTF Supertrend + EMA20 Pullback - Touch (100/200)",
    "source": "# btc-reviewed-mtf-pullback-v1 touch\n# 1H/15M Supertrend ATR 10 x 3, 15M EMA20.\n# Completed 1M touch from the trend side; enter next open.\n# 100-hour initialization; IST weekdays for entry, all days for exits.\n# One trade per contiguous aligned Supertrend cycle; no overlapping positions.\n# Fixed 100-point SL / 200-point TP from actual modeled fill.\n# No trailing stop or reversal exit. No live orders.\n# Reviewed SDK implementation; exposure defaults to 50% of equity.\nfrom btc_analysis.examples.mtf_pullback import MTFPullbackStrategy\n\nclass Strategy(MTFPullbackStrategy):\n    def __init__(self):\n        super().__init__(\"touch\")\n"
  },
  {
    "mode": "reclaim",
    "name": "MTF Supertrend + EMA20 Pullback - Reclaim (100/200)",
    "source": "# btc-reviewed-mtf-pullback-v1 reclaim\n# 1H/15M Supertrend ATR 10 x 3, 15M EMA20.\n# Completed 15M reclaim of EMA fixed at candle start; enter next open.\n# 100-hour initialization; IST weekdays for entry, all days for exits.\n# One trade per contiguous aligned Supertrend cycle; no overlapping positions.\n# Fixed 100-point SL / 200-point TP from actual modeled fill.\n# No trailing stop or reversal exit. No live orders.\n# Reviewed SDK implementation; exposure defaults to 50% of equity.\nfrom btc_analysis.examples.mtf_pullback import MTFPullbackStrategy\n\nclass Strategy(MTFPullbackStrategy):\n    def __init__(self):\n        super().__init__(\"reclaim\")\n"
  }
] as const;
