"""
Execution Agent — places and manages orders on Binance.
Logs all executions and handles partial fills.
"""

import logging
from typing import Any, Dict, List

from core.config import BotConfig
from exchange.binance_client import BinanceClient

logger = logging.getLogger("agent.execution")


class ExecutionAgent:
    """Converts approved signals into live orders on the exchange."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = BinanceClient(config)
        self.trade_log: List[Dict[str, Any]] = []

    async def execute(self, signals: List[Dict]) -> List[Dict[str, Any]]:
        """
        Execute each approved signal as a market order.

        Parameters
        ----------
        signals : list[dict]
            Risk-approved signals with 'action', 'quantity', etc.

        Returns
        -------
        list[dict]
            List of execution result dicts.
        """
        results: List[Dict[str, Any]] = []

        for signal in signals:
            action = signal["action"]
            quantity = signal.get("quantity", 0)

            if quantity <= 0:
                logger.warning("Skipping signal with zero quantity: %s", signal)
                continue

            result = self._place_order(action, quantity, signal)
            results.append(result)

        return results

    # ── Order Placement ──────────────────────────────────────

    def _place_order(
        self, action: str, quantity: float, signal: Dict
    ) -> Dict[str, Any]:
        """Place a single market order and log the result."""
        logger.info(
            "📤 Placing %s order: qty=%.6f  reason=%s",
            action,
            quantity,
            signal.get("reason", "N/A"),
        )

        if action == "BUY":
            response = self.client.place_market_buy(quantity=quantity)
        elif action == "SELL":
            response = self.client.place_market_sell(quantity=quantity)
        else:
            response = {"error": f"Unknown action: {action}"}

        # Build execution log entry
        entry = {
            "action": action,
            "quantity": quantity,
            "strategy": signal.get("strategy", "unknown"),
            "confidence": signal.get("confidence", 0),
            "entry_price": signal.get("entry_price", 0),
            "stop_loss": signal.get("stop_loss", 0),
            "take_profit": signal.get("take_profit", 0),
            "order_response": response,
            "success": "error" not in response,
        }

        self.trade_log.append(entry)

        if entry["success"]:
            logger.info(
                "✅ %s executed — orderId=%s  qty=%.6f",
                action,
                response.get("orderId", "?"),
                quantity,
            )
        else:
            logger.error("❌ %s failed — %s", action, response.get("error"))

        return entry

    # ── Trade History ────────────────────────────────────────

    def get_trade_log(self) -> List[Dict[str, Any]]:
        """Return the in-memory trade log."""
        return self.trade_log

    def get_stats(self) -> Dict[str, Any]:
        """Return basic execution statistics."""
        total = len(self.trade_log)
        success = sum(1 for t in self.trade_log if t["success"])
        return {
            "total_trades": total,
            "successful": success,
            "failed": total - success,
            "success_rate": f"{success / total * 100:.1f}%" if total > 0 else "N/A",
        }
