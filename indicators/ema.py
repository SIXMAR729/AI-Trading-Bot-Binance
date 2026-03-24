"""
EMA (Exponential Moving Average) indicator.
Gives more weight to recent prices for faster trend detection.
"""

import pandas as pd


def compute_ema(series: pd.Series, span: int = 20) -> pd.Series:
    """
    Calculate Exponential Moving Average.

    Parameters
    ----------
    series : pd.Series
        Price series.
    span : int
        EMA span / period.

    Returns
    -------
    pd.Series
        EMA values.
    """
    return series.ewm(span=span, adjust=False).mean()


def compute_double_ema(
    series: pd.Series, fast: int = 9, slow: int = 21
) -> pd.DataFrame:
    """
    Compute fast and slow EMAs for crossover detection.

    Parameters
    ----------
    series : pd.Series
        Price series.
    fast : int
        Fast EMA period.
    slow : int
        Slow EMA period.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'ema_fast' and 'ema_slow' columns.
    """
    return pd.DataFrame(
        {
            "ema_fast": compute_ema(series, fast),
            "ema_slow": compute_ema(series, slow),
        }
    )
