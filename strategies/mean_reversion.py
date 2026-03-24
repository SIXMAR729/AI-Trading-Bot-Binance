"""
Mean Reversion Strategy — Bollinger Bands.
Buys when price touches the lower band, sells when it touches the upper band.
"""

import logging
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger("strategy.mean_reversion")


class MeanReversionStrategy:
    """Bollinger Band-based mean reversion strategy."""

    NAME = "mean_reversion"

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    def evaluate(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Evaluate the latest data against Bollinger Bands.

        Expected DataFrame columns: close
        """
        if len(df) < self.period:
            return None

        close = df["close"]
        sma = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()

        upper_band = sma + self.std_dev * std
        lower_band = sma - self.std_dev * std

        current_price = close.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_sma = sma.iloc[-1]
        band_width = current_upper - current_lower

        if pd.isna(band_width) or band_width == 0:
            return None

        # Price at or below lower band → BUY (expect reversion to mean)
        if current_price <= current_lower:
            distance = (current_lower - current_price) / band_width
            confidence = min(0.5 + distance, 1.0)
            return {
                "strategy": self.NAME,
                "action": "BUY",
                "confidence": round(confidence, 4),
                "reason": (
                    f"Price ({current_price:.2f}) at/below lower "
                    f"Bollinger Band ({current_lower:.2f})"
                ),
            }

        # Price at or above upper band → SELL (expect reversion to mean)
        if current_price >= current_upper:
            distance = (current_price - current_upper) / band_width
            confidence = min(0.5 + distance, 1.0)
            return {
                "strategy": self.NAME,
                "action": "SELL",
                "confidence": round(confidence, 4),
                "reason": (
                    f"Price ({current_price:.2f}) at/above upper "
                    f"Bollinger Band ({current_upper:.2f})"
                ),
            }

        return None
