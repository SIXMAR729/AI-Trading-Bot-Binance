"""
Feature Agent — computes technical indicators on raw market data.
Attaches RSI, EMA, MACD columns to the DataFrame.
"""

import logging

import pandas as pd

from core.config import BotConfig
from indicators.rsi import compute_rsi
from indicators.ema import compute_ema, compute_double_ema
from indicators.macd import compute_macd

logger = logging.getLogger("agent.feature")


class FeatureAgent:
    """Enriches market data with technical indicators."""

    def __init__(self, config: BotConfig):
        self.config = config

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all indicators and attach them as new columns.

        Parameters
        ----------
        df : pd.DataFrame
            Raw OHLCV data with at least a 'close' column.

        Returns
        -------
        pd.DataFrame
            The same DataFrame with indicator columns appended.
        """
        close = df["close"]

        # ── RSI ──────────────────────────────────────────────
        df["rsi"] = compute_rsi(close, period=14)

        # ── EMA (fast / slow for crossover) ──────────────────
        emas = compute_double_ema(close, fast=9, slow=21)
        df["ema_fast"] = emas["ema_fast"]
        df["ema_slow"] = emas["ema_slow"]

        # ── MACD ─────────────────────────────────────────────
        macd = compute_macd(close, fast=12, slow=26, signal_period=9)
        df["macd_line"] = macd["macd_line"]
        df["macd_signal"] = macd["macd_signal"]
        df["macd_histogram"] = macd["macd_histogram"]

        # ── Additional features for ML ───────────────────────
        df["price_change"] = close.pct_change()
        df["volatility"] = close.rolling(window=20).std()
        df["volume_sma"] = df["volume"].rolling(window=20).mean()

        # Drop NaN rows from warm-up period
        df.dropna(inplace=True)

        logger.info("Computed %d indicator columns on %d rows", len(df.columns) - 5, len(df))
        return df
