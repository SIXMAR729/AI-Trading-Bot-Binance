"""
RSI (Relative Strength Index) indicator.
Measures the speed and magnitude of recent price changes.
"""

import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index.

    Parameters
    ----------
    series : pd.Series
        Price series (typically close prices).
    period : int
        Look-back period (default 14).

    Returns
    -------
    pd.Series
        RSI values between 0 and 100.
    """
    delta = series.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)  # avoid division by zero
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi
