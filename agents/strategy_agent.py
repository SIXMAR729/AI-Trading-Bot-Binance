"""
Strategy Agent — runs all enabled strategies and aggregates signals.
Optionally queries a pluggable ML model for additional prediction.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

from core.config import BotConfig
from strategies.trend_strategy import TrendStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum_strategy import MomentumStrategy

logger = logging.getLogger("agent.strategy")

# Registry of available strategies
STRATEGY_REGISTRY = {
    "trend": TrendStrategy,
    "mean_reversion": MeanReversionStrategy,
    "momentum": MomentumStrategy,
}


class StrategyAgent:
    """Evaluates multiple strategies and combines their signals."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.ml_model = None

        # Instantiate enabled strategies
        self.strategies = []
        for name in config.enabled_strategies:
            name = name.strip()
            cls = STRATEGY_REGISTRY.get(name)
            if cls:
                self.strategies.append(cls())
                logger.info("Loaded strategy: %s", name)
            else:
                logger.warning("Unknown strategy: %s (skipped)", name)

        # Load ML model if enabled
        if config.use_ml_model and config.ml_model_path:
            self._load_ml_model(config.ml_model_path)

    def evaluate(self, df: pd.DataFrame) -> List[Dict]:
        """
        Run all strategies against the enriched DataFrame.

        Returns
        -------
        list[dict]
            List of signal dicts from strategies that generated a signal.
            Each dict has: strategy, action, confidence, reason.
        """
        signals: List[Dict] = []

        # ── Rule-based strategies ────────────────────────────
        for strategy in self.strategies:
            try:
                signal = strategy.evaluate(df)
                if signal:
                    signals.append(signal)
                    logger.info(
                        "[%s] %s (confidence=%.2f): %s",
                        signal["strategy"],
                        signal["action"],
                        signal["confidence"],
                        signal["reason"],
                    )
            except Exception:
                logger.exception("Error in strategy %s", strategy.NAME)

        # ── ML model prediction ──────────────────────────────
        if self.ml_model:
            ml_signal = self._query_ml(df)
            if ml_signal:
                signals.append(ml_signal)

        # ── Aggregate: if majority agree, boost confidence ───
        if len(signals) >= 2:
            signals = self._aggregate(signals)

        return signals

    # ── ML Integration ───────────────────────────────────────

    def _load_ml_model(self, path: str) -> None:
        """Load a serialised ML model."""
        try:
            from ml.base_model import BasePredictionModel
            import joblib

            self.ml_model = joblib.load(path)
            logger.info("ML model loaded from %s", path)
        except Exception:
            logger.exception("Failed to load ML model from %s", path)
            self.ml_model = None

    def _query_ml(self, df: pd.DataFrame) -> Optional[Dict]:
        """Get a prediction from the ML model."""
        try:
            feature_cols = [
                "rsi", "ema_fast", "ema_slow",
                "macd_line", "macd_signal", "macd_histogram",
                "price_change", "volatility",
            ]
            available = [c for c in feature_cols if c in df.columns]
            if not available:
                return None

            X = df[available].iloc[-1:].values
            prediction = self.ml_model.predict(X)[0]
            proba = None

            if hasattr(self.ml_model, "predict_proba"):
                proba = self.ml_model.predict_proba(X)[0]

            action_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
            action = action_map.get(int(prediction), "HOLD")

            confidence = float(max(proba)) if proba is not None else 0.5

            if action == "HOLD":
                return None

            return {
                "strategy": "ml_model",
                "action": action,
                "confidence": round(confidence, 4),
                "reason": f"ML model prediction: {action} (confidence={confidence:.2%})",
            }
        except Exception:
            logger.exception("ML prediction failed")
            return None

    # ── Signal Aggregation ───────────────────────────────────

    @staticmethod
    def _aggregate(signals: List[Dict]) -> List[Dict]:
        """
        Aggregate signals — boost confidence when multiple strategies agree.
        Returns the strongest signal per action.
        """
        from collections import defaultdict

        by_action: Dict[str, List[Dict]] = defaultdict(list)
        for s in signals:
            by_action[s["action"]].append(s)

        aggregated = []
        for action, sigs in by_action.items():
            # Pick highest confidence, boost it if multiple agree
            best = max(sigs, key=lambda s: s["confidence"])
            agreement_bonus = 0.1 * (len(sigs) - 1)
            best["confidence"] = round(min(best["confidence"] + agreement_bonus, 1.0), 4)
            best["reason"] += f" (+{len(sigs)} strategies agree)"
            aggregated.append(best)

        return aggregated
