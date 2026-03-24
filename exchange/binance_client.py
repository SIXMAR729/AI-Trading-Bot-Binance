"""
Binance exchange client — wraps python-binance for the trading bot.
Supports both live and testnet endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from core.config import BotConfig

logger = logging.getLogger("binance_client")

# Binance testnet base URLs
TESTNET_API_URL = "https://testnet.binance.vision/api"
TESTNET_WS_URL = "wss://testnet.binance.vision/ws"


class BinanceClient:
    """Unified interface to the Binance REST API."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.symbol = config.symbol

        if config.use_testnet:
            self.client = Client(
                config.api_key,
                config.api_secret,
                testnet=True,
            )
            logger.info("Connected to Binance TESTNET")
        else:
            self.client = Client(config.api_key, config.api_secret)
            logger.info("Connected to Binance LIVE")

    # ── Market Data ──────────────────────────────────────────

    def get_klines(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """Fetch OHLCV candles and return as a DataFrame."""
        symbol = symbol or self.symbol
        interval = interval or self.config.timeframe

        try:
            raw = self.client.get_klines(
                symbol=symbol, interval=interval, limit=limit
            )
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to fetch klines: %s", exc)
            return pd.DataFrame()

        df = pd.DataFrame(
            raw,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        df.set_index("open_time", inplace=True)

        return df[["open", "high", "low", "close", "volume"]]

    def get_ticker_price(self, symbol: Optional[str] = None) -> float:
        """Get current market price."""
        symbol = symbol or self.symbol
        try:
            tick = self.client.get_symbol_ticker(symbol=symbol)
            return float(tick["price"])
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to get ticker: %s", exc)
            return 0.0

    # ── Account ──────────────────────────────────────────────

    def get_balance(self, asset: str = "USDT") -> float:
        """Get free balance for an asset."""
        try:
            info = self.client.get_asset_balance(asset=asset)
            return float(info["free"]) if info else 0.0
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to get balance: %s", exc)
            return 0.0

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Return open orders for the symbol."""
        symbol = symbol or self.symbol
        try:
            return self.client.get_open_orders(symbol=symbol)
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to get open orders: %s", exc)
            return []

    # ── Order Management ─────────────────────────────────────

    def place_market_buy(
        self, symbol: Optional[str] = None, quantity: float = 0.0
    ) -> Dict[str, Any]:
        """Place a MARKET BUY order."""
        symbol = symbol or self.symbol
        try:
            order = self.client.order_market_buy(
                symbol=symbol, quantity=self._format_qty(quantity)
            )
            logger.info("BUY order placed: %s", order.get("orderId"))
            return order
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("BUY order failed: %s", exc)
            return {"error": str(exc)}

    def place_market_sell(
        self, symbol: Optional[str] = None, quantity: float = 0.0
    ) -> Dict[str, Any]:
        """Place a MARKET SELL order."""
        symbol = symbol or self.symbol
        try:
            order = self.client.order_market_sell(
                symbol=symbol, quantity=self._format_qty(quantity)
            )
            logger.info("SELL order placed: %s", order.get("orderId"))
            return order
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("SELL order failed: %s", exc)
            return {"error": str(exc)}

    def place_limit_buy(
        self,
        price: float,
        quantity: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place a LIMIT BUY order."""
        symbol = symbol or self.symbol
        try:
            order = self.client.order_limit_buy(
                symbol=symbol,
                quantity=self._format_qty(quantity),
                price=self._format_price(price),
            )
            logger.info("LIMIT BUY placed: %s @ %s", order.get("orderId"), price)
            return order
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("LIMIT BUY failed: %s", exc)
            return {"error": str(exc)}

    def place_limit_sell(
        self,
        price: float,
        quantity: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Place a LIMIT SELL order."""
        symbol = symbol or self.symbol
        try:
            order = self.client.order_limit_sell(
                symbol=symbol,
                quantity=self._format_qty(quantity),
                price=self._format_price(price),
            )
            logger.info("LIMIT SELL placed: %s @ %s", order.get("orderId"), price)
            return order
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("LIMIT SELL failed: %s", exc)
            return {"error": str(exc)}

    def cancel_order(
        self, order_id: int, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an open order by ID."""
        symbol = symbol or self.symbol
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info("Order %s cancelled", order_id)
            return result
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Cancel failed for %s: %s", order_id, exc)
            return {"error": str(exc)}

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _format_qty(qty: float) -> str:
        """Format quantity to 6 decimals (Binance precision)."""
        return f"{qty:.6f}"

    @staticmethod
    def _format_price(price: float) -> str:
        """Format price to 2 decimals."""
        return f"{price:.2f}"
