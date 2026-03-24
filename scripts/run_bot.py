#!/usr/bin/env python3
"""
run_bot.py — Entry point for the AI Trading Bot.

Usage:
    python scripts/run_bot.py              # Paper trading (default)
    python scripts/run_bot.py --live       # Live trading on Binance
    python scripts/run_bot.py --backtest   # Backtest using cached data
"""

import argparse
import asyncio
import logging
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import BotConfig
from core.orchestrator import Orchestrator


# ── Logging Setup ────────────────────────────────────────────

def setup_logging(level: str = "INFO") -> None:
    """Configure structured console logging."""
    fmt = "%(asctime)s │ %(levelname)-7s │ %(name)-20s │ %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


# ── CLI ──────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Trading Bot — Multi-agent BTC/USDT trader"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help="Run in LIVE mode (real money, real orders)",
    )
    mode.add_argument(
        "--paper",
        action="store_true",
        default=True,
        help="Run in PAPER mode (testnet, no real orders) [default]",
    )
    mode.add_argument(
        "--backtest",
        action="store_true",
        help="Run backtest on cached historical data",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Trading pair symbol (e.g. BTCUSDT)",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default=None,
        help="Candle interval (e.g. 1h, 15m, 1d)",
    )
    return parser.parse_args()


# ── Main ─────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    config = BotConfig()

    # Override config with CLI args
    if args.live:
        config.use_testnet = False
    elif args.paper:
        config.use_testnet = True

    if args.symbol:
        config.symbol = args.symbol
    if args.interval:
        config.timeframe = args.interval

    setup_logging(config.log_level)
    logger = logging.getLogger("run_bot")

    # ── Banner ───────────────────────────────────────────
    mode_str = "🔴 LIVE" if not config.use_testnet else "🟢 PAPER (testnet)"
    logger.info("╔════════════════════════════════════════════╗")
    logger.info("║         AI TRADING BOT  v1.0               ║")
    logger.info("╚════════════════════════════════════════════╝")
    logger.info("Mode:     %s", mode_str)
    logger.info("Symbol:   %s", config.symbol)
    logger.info("Interval: %s", config.timeframe)
    logger.info("Strategies: %s", ", ".join(config.enabled_strategies))
    logger.info("Risk/Trade: %.1f%%", config.risk_per_trade * 100)
    logger.info("ML Model:  %s", "Enabled" if config.use_ml_model else "Disabled")

    # ── Safety check for live trading ────────────────────
    if not config.use_testnet:
        logger.warning("⚠️  LIVE TRADING MODE — Real money at risk!")
        try:
            confirm = input("Type 'YES' to confirm live trading: ")
            if confirm.strip() != "YES":
                logger.info("Aborted by user")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            logger.info("Aborted")
            sys.exit(0)

    # ── Validate config ──────────────────────────────────
    try:
        config.validate()
    except ValueError as exc:
        logger.error("❌ %s", exc)
        sys.exit(1)

    # ── Backtest mode ────────────────────────────────────
    if args.backtest:
        logger.info("Backtest mode not yet implemented — coming soon!")
        sys.exit(0)

    # ── Run the orchestrator ─────────────────────────────
    orchestrator = Orchestrator(config)

    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user — shutting down …")
        orchestrator.stop()


if __name__ == "__main__":
    main()
