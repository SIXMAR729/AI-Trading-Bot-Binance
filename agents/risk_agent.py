"""
Risk Agent — enforces position sizing, stop-loss, take-profit,
daily loss limits, and trade cooldowns.
"""

import logging
import time
from typing import Dict, List

import pandas as pd

from core.config import BotConfig
from exchange.binance_client import BinanceClient

logger = logging.getLogger("agent.risk")


class RiskAgent:
    """Filters and sizes trades based on risk management rules."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = BinanceClient(config)

        # State tracking
        self._last_trade_time: float = 0.0
        self._daily_pnl: float = 0.0
        self._daily_reset_day: int = -1  # day of month for daily PnL reset

    def assess(self, signals: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """
        Evaluate each signal against risk rules.
        Approved signals get a 'quantity' field added.

        Parameters
        ----------
        signals : list[dict]
            Raw signals from the strategy agent.
        df : pd.DataFrame
            Current market data with indicators.

        Returns
        -------
        list[dict]
            Signals that passed risk checks, with 'quantity' appended.
        """
        self._reset_daily_if_needed()

        approved: List[Dict] = []
        for signal in signals:
            if self._check_signal(signal, df):
                approved.append(signal)

        return approved

    # ── Risk Checks ──────────────────────────────────────────

    def _check_signal(self, signal: Dict, df: pd.DataFrame) -> bool:
        """Run all risk checks on a single signal."""
        action = signal["action"]

        # 1. Trade cooldown
        now = time.time()
        if now - self._last_trade_time < self.config.trade_cooldown_seconds:
            remaining = self.config.trade_cooldown_seconds - (now - self._last_trade_time)
            logger.info("⏳ Cooldown active — %.0fs remaining", remaining)
            return False

        # 2. Daily loss limit
        if self._daily_pnl <= -self.config.max_daily_loss:
            logger.warning(
                "🚫 Daily loss limit hit (PnL=%.4f, limit=%.4f)",
                self._daily_pnl,
                self.config.max_daily_loss,
            )
            return False

        # 3. Position sizing
        current_price = df["close"].iloc[-1]
        balance = self.client.get_balance("USDT")

        if balance <= 0:
            logger.warning("No USDT balance available")
            return False

        # Calculate position size: risk_per_trade % of balance
        risk_amount = balance * self.config.risk_per_trade
        max_position = balance * self.config.max_position_pct

        # Size based on stop-loss distance
        stop_distance = current_price * self.config.stop_loss_pct
        if stop_distance > 0:
            quantity = risk_amount / stop_distance
        else:
            quantity = risk_amount / current_price

        # Cap at max position percentage
        max_qty = max_position / current_price
        quantity = min(quantity, max_qty)

        if quantity <= 0:
            logger.warning("Calculated quantity is zero or negative")
            return False

        # 4. Minimum confidence threshold
        if signal.get("confidence", 0) < 0.3:
            logger.info(
                "Signal confidence too low (%.2f < 0.30)", signal["confidence"]
            )
            return False

        # Attach trade size and risk levels to the signal
        signal["quantity"] = round(quantity, 6)
        signal["stop_loss"] = round(
            current_price * (1 - self.config.stop_loss_pct)
            if action == "BUY"
            else current_price * (1 + self.config.stop_loss_pct),
            2,
        )
        signal["take_profit"] = round(
            current_price * (1 + self.config.take_profit_pct)
            if action == "BUY"
            else current_price * (1 - self.config.take_profit_pct),
            2,
        )
        signal["entry_price"] = round(current_price, 2)

        logger.info(
            "✅ Risk approved: %s %.6f @ %.2f  SL=%.2f  TP=%.2f",
            action,
            signal["quantity"],
            current_price,
            signal["stop_loss"],
            signal["take_profit"],
        )

        self._last_trade_time = now
        return True

    # ── Daily Reset ──────────────────────────────────────────

    def _reset_daily_if_needed(self) -> None:
        """Reset daily PnL counter at the start of a new day."""
        import datetime

        today = datetime.datetime.utcnow().day
        if today != self._daily_reset_day:
            self._daily_pnl = 0.0
            self._daily_reset_day = today
            logger.info("Daily PnL reset")

    def record_pnl(self, pnl: float) -> None:
        """Record profit/loss from a completed trade."""
        self._daily_pnl += pnl
        logger.info("Daily PnL updated: %.4f", self._daily_pnl)
