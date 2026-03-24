"""
Configuration management for the AI Trading Bot.
Loads settings from environment variables / .env file.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Central configuration for the trading bot."""

    # ── Binance API ──────────────────────────────────────────
    api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    use_testnet: bool = field(
        default_factory=lambda: os.getenv("USE_TESTNET", "true").lower() == "true"
    )

    # ── Trading parameters ───────────────────────────────────
    symbol: str = field(default_factory=lambda: os.getenv("TRADING_SYMBOL", "BTCUSDT"))
    timeframe: str = field(default_factory=lambda: os.getenv("TIMEFRAME", "1h"))
    lookback_periods: int = field(
        default_factory=lambda: int(os.getenv("LOOKBACK_PERIODS", "100"))
    )

    # ── Strategy selection ───────────────────────────────────
    enabled_strategies: List[str] = field(
        default_factory=lambda: os.getenv(
            "ENABLED_STRATEGIES", "trend,mean_reversion,momentum"
        ).split(",")
    )

    # ── Risk management ──────────────────────────────────────
    risk_per_trade: float = field(
        default_factory=lambda: float(os.getenv("RISK_PER_TRADE", "0.02"))
    )
    max_position_pct: float = field(
        default_factory=lambda: float(os.getenv("MAX_POSITION_PCT", "0.10"))
    )
    max_daily_loss: float = field(
        default_factory=lambda: float(os.getenv("MAX_DAILY_LOSS", "0.05"))
    )
    stop_loss_pct: float = field(
        default_factory=lambda: float(os.getenv("STOP_LOSS_PCT", "0.03"))
    )
    take_profit_pct: float = field(
        default_factory=lambda: float(os.getenv("TAKE_PROFIT_PCT", "0.06"))
    )
    trade_cooldown_seconds: int = field(
        default_factory=lambda: int(os.getenv("TRADE_COOLDOWN_SECONDS", "300"))
    )

    # ── ML model ─────────────────────────────────────────────
    use_ml_model: bool = field(
        default_factory=lambda: os.getenv("USE_ML_MODEL", "false").lower() == "true"
    )
    ml_model_path: Optional[str] = field(
        default_factory=lambda: os.getenv("ML_MODEL_PATH", None)
    )

    # ── Orchestrator ─────────────────────────────────────────
    loop_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("LOOP_INTERVAL_SECONDS", "60"))
    )

    # ── Database ─────────────────────────────────────────────
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "data/market_cache.db")
    )

    # ── Logging ──────────────────────────────────────────────
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def validate(self) -> None:
        """Validate critical config before starting the bot."""
        errors: List[str] = []
        if not self.api_key:
            errors.append("BINANCE_API_KEY is not set")
        if not self.api_secret:
            errors.append("BINANCE_API_SECRET is not set")
        if self.risk_per_trade <= 0 or self.risk_per_trade > 1:
            errors.append("RISK_PER_TRADE must be between 0 and 1")
        if self.max_position_pct <= 0 or self.max_position_pct > 1:
            errors.append("MAX_POSITION_PCT must be between 0 and 1")
        if errors:
            raise ValueError(
                "Configuration errors:\n  • " + "\n  • ".join(errors)
            )
