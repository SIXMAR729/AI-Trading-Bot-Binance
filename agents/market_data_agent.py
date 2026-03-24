"""
Market Data Agent — fetches live OHLCV data from Binance
and caches it in a local SQLite database.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from core.config import BotConfig
from exchange.binance_client import BinanceClient

logger = logging.getLogger("agent.market_data")


class MarketDataAgent:
    """Responsible for fetching and caching market data."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = BinanceClient(config)

        # Ensure data directory exists
        db_path = Path(config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self._init_db()

    # ── Public ───────────────────────────────────────────────

    async def fetch(self) -> Optional[pd.DataFrame]:
        """
        Fetch the latest klines from Binance and cache them.

        Returns
        -------
        pd.DataFrame | None
            OHLCV DataFrame or None on failure.
        """
        df = self.client.get_klines(
            symbol=self.config.symbol,
            interval=self.config.timeframe,
            limit=self.config.lookback_periods,
        )

        if df.empty:
            logger.warning("Received empty klines from Binance")
            return None

        self._cache(df)
        logger.info(
            "Fetched %d candles for %s (%s)",
            len(df),
            self.config.symbol,
            self.config.timeframe,
        )
        return df

    # ── Cache ────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Create the klines cache table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS klines (
                    symbol      TEXT    NOT NULL,
                    timeframe   TEXT    NOT NULL,
                    open_time   TEXT    NOT NULL,
                    open        REAL,
                    high        REAL,
                    low         REAL,
                    close       REAL,
                    volume      REAL,
                    PRIMARY KEY (symbol, timeframe, open_time)
                )
                """
            )

    def _cache(self, df: pd.DataFrame) -> None:
        """Upsert rows into the klines cache."""
        rows = []
        for ts, row in df.iterrows():
            rows.append(
                (
                    self.config.symbol,
                    self.config.timeframe,
                    str(ts),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                )
            )
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO klines
                    (symbol, timeframe, open_time, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        logger.debug("Cached %d rows to SQLite", len(rows))

    def load_cached(
        self, symbol: Optional[str] = None, timeframe: Optional[str] = None, limit: int = 500
    ) -> pd.DataFrame:
        """Load cached klines from SQLite."""
        symbol = symbol or self.config.symbol
        timeframe = timeframe or self.config.timeframe
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                """
                SELECT open_time, open, high, low, close, volume
                FROM klines
                WHERE symbol = ? AND timeframe = ?
                ORDER BY open_time DESC
                LIMIT ?
                """,
                conn,
                params=(symbol, timeframe, limit),
            )
        if not df.empty:
            df["open_time"] = pd.to_datetime(df["open_time"])
            df.set_index("open_time", inplace=True)
            df.sort_index(inplace=True)
        return df
