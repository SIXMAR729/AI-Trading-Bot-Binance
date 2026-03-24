"""
Orchestrator — the central coordinator of all trading agents.
Runs the main loop: fetch → features → strategy → risk → execute.
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from core.config import BotConfig
from agents.market_data_agent import MarketDataAgent
from agents.feature_agent import FeatureAgent
from agents.strategy_agent import StrategyAgent
from agents.risk_agent import RiskAgent
from agents.execution_agent import ExecutionAgent

logger = logging.getLogger("orchestrator")


class Orchestrator:
    """Coordinates the full trading pipeline in an async loop."""

    def __init__(self, config: BotConfig):
        self.config = config
        self._running = False

        # ── Agents ───────────────────────────────────────────
        self.market_data_agent = MarketDataAgent(config)
        self.feature_agent = FeatureAgent(config)
        self.strategy_agent = StrategyAgent(config)
        self.risk_agent = RiskAgent(config)
        self.execution_agent = ExecutionAgent(config)

        logger.info("Orchestrator initialised — symbol=%s  tf=%s", config.symbol, config.timeframe)

    # ── Public API ───────────────────────────────────────────

    async def start(self) -> None:
        """Start the main trading loop."""
        self._running = True
        self._register_signal_handlers()
        logger.info("🚀 Bot started at %s", datetime.utcnow().isoformat())

        while self._running:
            cycle_start = time.monotonic()
            try:
                await self._run_cycle()
            except Exception:
                logger.exception("‼️  Error in trading cycle")

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0, self.config.loop_interval_seconds - elapsed)
            if self._running and sleep_time > 0:
                logger.debug("Sleeping %.1fs until next cycle", sleep_time)
                await asyncio.sleep(sleep_time)

        logger.info("🛑 Bot stopped gracefully")

    def stop(self) -> None:
        """Request a graceful shutdown."""
        logger.info("Shutdown requested …")
        self._running = False

    # ── Core Cycle ───────────────────────────────────────────

    async def _run_cycle(self) -> None:
        """Execute one full trading cycle."""
        logger.info("═══ Cycle start %s ═══", datetime.utcnow().strftime("%H:%M:%S"))

        # 1. Fetch market data
        df = await self.market_data_agent.fetch()
        if df is None or df.empty:
            logger.warning("No market data received — skipping cycle")
            return

        logger.info("📊 Received %d candles", len(df))

        # 2. Compute features / indicators
        df = self.feature_agent.compute(df)
        logger.info("🔬 Features computed — columns: %s", list(df.columns))

        # 3. Generate strategy signals
        signals = self.strategy_agent.evaluate(df)
        logger.info("📡 Signals: %s", signals)

        if not signals:
            logger.info("No actionable signals — holding")
            return

        # 4. Risk checks
        approved = self.risk_agent.assess(signals, df)
        logger.info("🛡️  Risk-approved signals: %s", approved)

        if not approved:
            logger.info("All signals rejected by risk agent")
            return

        # 5. Execute trades
        results = await self.execution_agent.execute(approved)
        for r in results:
            logger.info("✅ Execution result: %s", r)

    # ── Signal Handlers ──────────────────────────────────────

    def _register_signal_handlers(self) -> None:
        """Register OS-level signals for graceful shutdown."""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self.stop)
        # On Windows, KeyboardInterrupt is caught in run_bot.py
