"""Trend-following signals for one stock. Analysis only; places no orders.

Usage: python3 trend_following.py prices.csv [--account 10000] [--risk 0.01]
CSV columns: date, high, low, close (case-insensitive).

Signals (all on closing prices):
  Trend filter : price above 200-day average AND 50-day above 200-day
  Strength     : ADX(14) > 25 strong trend, < 20 no trend (use mean reversion instead)
  Entry        : close breaks above the 20-day high (Donchian breakout)
  Exit         : close breaks below the 10-day low, or below the ATR stop
  Sizing       : shares = (account * risk) / (2 * ATR(14))
"""
import argparse
import numpy as np
import pandas as pd


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df[["date", "high", "low", "close"]].reset_index(drop=True)


def atr(df, n=14):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def adx(df, n=14):
    up = df["high"].diff()
    down = -df["low"].diff()
    plus = np.where((up > down) & (up > 0), up, 0.0)
    minus = np.where((down > up) & (down > 0), down, 0.0)
    a = atr(df, n)
    pdi = 100 * pd.Series(plus).ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * pd.Series(minus).ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def analyze(df, account=10000.0, risk=0.01, entry_n=20, exit_n=10):
    d = df.copy()
    d["sma50"] = d["close"].rolling(50).mean()
    d["sma200"] = d["close"].rolling(200).mean()
    d["hi_entry"] = d["high"].rolling(entry_n).max().shift(1)
    d["lo_exit"] = d["low"].rolling(exit_n).min().shift(1)
    d["atr"] = atr(d)
    d["adx"] = adx(d)
    last = d.iloc[-1]
    uptrend = last.close > last.sma200 and last.sma50 > last.sma200
    downtrend = last.close < last.sma200 and last.sma50 < last.sma200
    strength = "strong" if last.adx > 25 else "none" if last.adx < 20 else "developing"
    if uptrend:
        trend = "Uptrend"
    elif downtrend:
        trend = "Downtrend"
    else:
        trend = "Mixed"
    if uptrend and last.close > last.hi_entry:
        action = "ENTRY signal (breakout above %d-day high)" % entry_n
    elif last.close < last.lo_exit:
        action = "EXIT signal (broke below %d-day low)" % exit_n
    else:
        action = "No new signal"
    stop = last.close - 2 * last.atr
    shares = int((account * risk) / (2 * last.atr)) if last.atr > 0 else 0
    return {
        "date": last.date, "close": round(last.close, 2), "trend": trend,
        "adx": round(last.adx, 1), "trend_strength": strength,
        "suggests": "trend following" if strength == "strong" else "mean reversion / stay out" if strength == "none" else "wait",
        "action": action, "atr_stop": round(stop, 2), "position_size_shares": shares,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--account", type=float, default=10000)
    ap.add_argument("--risk", type=float, default=0.01, help="fraction of account risked per trade")
    a = ap.parse_args()
    for k, v in analyze(load(a.csv), a.account, a.risk).items():
        print(f"{k}: {v}")
