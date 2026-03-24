"""
MACD (Moving Average Convergence Divergence) indicator.
Reveals changes in trend strength, direction, momentum, and duration.
"""

import pandas as pd


def compute_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """
    Calculate MACD line, signal line, and histogram.

    Parameters
    ----------
    series : pd.Series
        Price series (typically close prices).
    fast : int
        Fast EMA period (default 12).
    slow : int
        Slow EMA period (default 26).
    signal_period : int
        Signal line EMA period (default 9).

    Returns
    -------
    pd.DataFrame
        Columns: macd_line, macd_signal, macd_histogram.
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {
            "macd_line": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
        }
    )
