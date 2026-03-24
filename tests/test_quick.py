"""Quick verification of indicator computations."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from indicators.rsi import compute_rsi
from indicators.ema import compute_ema
from indicators.macd import compute_macd

prices = pd.Series([100,102,101,103,105,104,106,108,107,109,111,110,112,114,113,115,117,116,118,120])

rsi = compute_rsi(prices, 14)
print(f"RSI last value: {rsi.iloc[-1]:.1f}")

ema = compute_ema(prices, 9)
print(f"EMA last value: {ema.iloc[-1]:.1f}")

macd = compute_macd(prices)
print(f"MACD line: {macd['macd_line'].iloc[-1]:.4f}")
print(f"MACD signal: {macd['macd_signal'].iloc[-1]:.4f}")

print("\nAll indicators computed successfully!")
