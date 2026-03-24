# 🤖 AI Trading Bot

A modular, multi-agent AI trading bot for **BTC/USDT on Binance** with pluggable ML/AI support.

---

## ⚡ Architecture

```
                    ┌──────────────┐
                    │  run_bot.py  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Orchestrator │ ← Main async loop
                    └──┬──┬──┬──┬─┘
          ┌────────────┘  │  │  └────────────┐
          ▼               ▼  ▼               ▼
  ┌───────────────┐ ┌─────────────┐ ┌──────────────┐
  │ Market Data   │ │  Feature    │ │  Strategy    │
  │ Agent         │ │  Agent      │ │  Agent       │
  └───────┬───────┘ └──────┬──────┘ └──────┬───────┘
          │                │               │
          ▼                ▼               ▼
  ┌───────────────┐ ┌─────────────┐ ┌──────────────┐
  │ Binance API   │ │ RSI/EMA/    │ │ Trend/MeanR/ │
  │ + SQLite      │ │ MACD        │ │ Momentum+ML  │
  └───────────────┘ └─────────────┘ └──────────────┘
          │                               │
          │         ┌─────────────┐       │
          │         │  Risk Agent │◄──────┘
          │         └──────┬──────┘
          │                │
          │         ┌──────▼──────┐
          └────────►│ Execution   │──► Binance Orders
                    │ Agent       │
                    └─────────────┘
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd Ai-trading-bot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Binance API keys
```

### 3. Run

```bash
# Paper trading (testnet — no real money)
python scripts/run_bot.py --paper

# Live trading (requires API keys + confirmation)
python scripts/run_bot.py --live

# Custom symbol / interval
python scripts/run_bot.py --paper --symbol ETHUSDT --interval 15m
```

---

## 📂 Project Structure

```
ai-trading-bot/
├── agents/                    # Trading agents
│   ├── market_data_agent.py   # Fetches OHLCV from Binance
│   ├── feature_agent.py       # Computes RSI, EMA, MACD
│   ├── strategy_agent.py      # Runs strategies, aggregates signals
│   ├── risk_agent.py          # Position sizing, stop-loss, limits
│   └── execution_agent.py     # Places orders on Binance
│
├── strategies/                # Trading strategies
│   ├── trend_strategy.py      # Dual EMA crossover
│   ├── mean_reversion.py      # Bollinger Bands
│   └── momentum_strategy.py   # RSI + MACD dual confirmation
│
├── indicators/                # Technical indicators
│   ├── rsi.py                 # Relative Strength Index
│   ├── ema.py                 # Exponential Moving Average
│   └── macd.py                # MACD line/signal/histogram
│
├── exchange/                  # Exchange integration
│   └── binance_client.py      # python-binance wrapper
│
├── ml/                        # AI/ML integration
│   ├── base_model.py          # Abstract model interface
│   └── sklearn_model.py       # RandomForest example
│
├── core/                      # Core components
│   ├── config.py              # Environment-based config
│   └── orchestrator.py        # Main trading loop
│
├── data/                      # Auto-created data dir
│   └── market_cache.db        # SQLite kline cache
│
├── scripts/
│   └── run_bot.py             # CLI entry point
│
├── .env.example               # Config template
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🧠 Strategies

| Strategy | Method | Buy Signal | Sell Signal |
|----------|--------|------------|-------------|
| **Trend** | EMA Crossover (9/21) | Fast EMA > Slow EMA | Fast EMA < Slow EMA |
| **Mean Reversion** | Bollinger Bands (20, 2σ) | Price ≤ Lower Band | Price ≥ Upper Band |
| **Momentum** | RSI + MACD | RSI < 30 + MACD bullish cross | RSI > 70 + MACD bearish cross |

Signals include a **confidence score** (0–1). When multiple strategies agree, confidence is boosted.

---

## 🛡️ Risk Management

- **Position sizing** — Risk only `RISK_PER_TRADE` % of balance per trade
- **Max position** — Never exceed `MAX_POSITION_PCT` % of balance
- **Stop-loss / Take-profit** — Automatically calculated per trade
- **Daily loss limit** — Bot stops trading if daily loss exceeds `MAX_DAILY_LOSS` %
- **Trade cooldown** — Minimum `TRADE_COOLDOWN_SECONDS` between trades
- **Confidence threshold** — Signals below 30% confidence are rejected

---

## 🤖 AI/ML Integration

The bot supports pluggable ML models. To add your own:

1. Subclass `ml.base_model.BasePredictionModel`
2. Implement `train()`, `predict()`, `save()`, `load()`
3. Train your model and save it
4. Set `USE_ML_MODEL=true` and `ML_MODEL_PATH=path/to/model.pkl` in `.env`

### Supported Frameworks

- ✅ scikit-learn (included example)
- ✅ TensorFlow / Keras
- ✅ PyTorch
- ✅ XGBoost / LightGBM
- ✅ Any framework that fits the interface

---

## ⚠️ Disclaimer

> **This bot trades with real money in live mode.** Cryptocurrency trading involves substantial risk of loss. The developers are not responsible for any financial losses incurred through the use of this software. Always:
> - Test thoroughly in **paper mode** first
> - Never risk more than you can afford to lose
> - Monitor the bot while it's running
> - Start with minimum position sizes
