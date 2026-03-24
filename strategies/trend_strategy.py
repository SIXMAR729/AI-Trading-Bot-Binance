"""
Trend Following Strategy — Dual EMA Crossover.
Buys when fast EMA crosses above slow EMA, sells when it crosses below.
"""

import logging
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger("strategy.trend")


class TrendStrategy:
    """EMA crossover trend-following strategy."""

    NAME = "trend"

    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def evaluate(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Evaluate the latest data and return a signal dict or None.

        Expected DataFrame columns: ema_fast, ema_slow
        """
        if "ema_fast" not in df.columns or "ema_slow" not in df.columns:
            logger.warning("Missing EMA columns — skipping trend strategy")
            return None

        if len(df) < 2:
            return None

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        prev_diff = prev["ema_fast"] - prev["ema_slow"]
        curr_diff = curr["ema_fast"] - curr["ema_slow"]

        # Bullish crossover
        if prev_diff <= 0 and curr_diff > 0:
            confidence = min(abs(curr_diff) / curr["ema_slow"] * 1000, 1.0)
            return {
                "strategy": self.NAME,
                "action": "BUY",
                "confidence": round(confidence, 4),
                "reason": f"Fast EMA crossed above Slow EMA (diff={curr_diff:.4f})",
            }

        # Bearish crossover
        if prev_diff >= 0 and curr_diff < 0:
            confidence = min(abs(curr_diff) / curr["ema_slow"] * 1000, 1.0)
            return {
                "strategy": self.NAME,
                "action": "SELL",
                "confidence": round(confidence, 4),
                "reason": f"Fast EMA crossed below Slow EMA (diff={curr_diff:.4f})",
            }

        return None
