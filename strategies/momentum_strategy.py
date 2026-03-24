"""
Momentum Strategy — RSI + MACD dual confirmation.
Requires both RSI and MACD to agree before generating a signal.
"""

import logging
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger("strategy.momentum")


class MomentumStrategy:
    """RSI + MACD momentum strategy with dual confirmation."""

    NAME = "momentum"

    def __init__(
        self,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
    ):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def evaluate(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Evaluate momentum using RSI + MACD confirmation.

        Expected DataFrame columns: rsi, macd_line, macd_signal
        """
        required = {"rsi", "macd_line", "macd_signal"}
        if not required.issubset(df.columns):
            logger.warning("Missing required columns for momentum strategy")
            return None

        if len(df) < 2:
            return None

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = curr["rsi"]
        macd = curr["macd_line"]
        signal = curr["macd_signal"]
        prev_macd = prev["macd_line"]
        prev_signal = prev["macd_signal"]

        # ── Bullish: RSI oversold + MACD bullish crossover ───
        rsi_bullish = rsi < self.rsi_oversold
        macd_bullish = prev_macd <= prev_signal and macd > signal

        if rsi_bullish and macd_bullish:
            # Confidence higher when RSI is more oversold
            rsi_conf = (self.rsi_oversold - rsi) / self.rsi_oversold
            macd_conf = min(abs(macd - signal) / (abs(signal) + 1e-10), 1.0)
            confidence = (rsi_conf + macd_conf) / 2
            return {
                "strategy": self.NAME,
                "action": "BUY",
                "confidence": round(min(confidence, 1.0), 4),
                "reason": (
                    f"RSI oversold ({rsi:.1f}) + MACD bullish crossover "
                    f"(MACD={macd:.4f}, Signal={signal:.4f})"
                ),
            }

        # ── Bearish: RSI overbought + MACD bearish crossover ─
        rsi_bearish = rsi > self.rsi_overbought
        macd_bearish = prev_macd >= prev_signal and macd < signal

        if rsi_bearish and macd_bearish:
            rsi_conf = (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            macd_conf = min(abs(macd - signal) / (abs(signal) + 1e-10), 1.0)
            confidence = (rsi_conf + macd_conf) / 2
            return {
                "strategy": self.NAME,
                "action": "SELL",
                "confidence": round(min(confidence, 1.0), 4),
                "reason": (
                    f"RSI overbought ({rsi:.1f}) + MACD bearish crossover "
                    f"(MACD={macd:.4f}, Signal={signal:.4f})"
                ),
            }

        return None
