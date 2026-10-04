"""RSI (Relative Strength Index) signals + divergences for one stock. Analysis only; places no orders.

Usage: python3 rsi.py prices.csv [--period 14] [--market-cap 5e9] [--avg-volume 2e6] [--catalyst yes|no|unknown]
CSV columns: date, close (high/low optional), volume optional. DAILY or WEEKLY bars only.

Guardrails (the script refuses or warns, it never fakes a signal):
  - Intraday bars (5/10-minute etc.) are rejected.
  - Fewer than 120 bars: too short, RSI unreliable.
  - Penny / illiquid stocks (price < $5, market cap < $300M, avg volume < 500k): rejected.
  - Jumpy price (a daily move > 4 standard deviations, or > 15%): warned, RSI may mislead.
  - A news/earnings catalyst in the window: signal marked "not organic".
"""
import argparse
import numpy as np
import pandas as pd


def rsi(close, n=14):
    """Wilder's RSI, 0-100."""
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0).where(gain.notna())


def hayden_regime(v):
    return "bullish (RSI > 60)" if v > 60 else "bearish (RSI < 40)" if v < 40 else "sideways (RSI 40-60)"


def pivots(s, k=5):
    """Indices of swing highs and lows (extreme over k bars each side; confirmed k bars later)."""
    hi, lo = [], []
    for i in range(k, len(s) - k):
        w = s.iloc[i - k:i + k + 1]
        if s.iloc[i] == w.max():
            hi.append(i)
        if s.iloc[i] == w.min():
            lo.append(i)
    return hi, lo


def divergences(close, r, k=5):
    """Bearish: price higher high, RSI lower high. Bullish: price lower low, RSI higher low."""
    hi, lo = pivots(close, k)
    out = []
    for a, b in zip(hi, hi[1:]):
        if close[b] > close[a] and r[b] < r[a] and not np.isnan(r[a]):
            out.append(("bearish", b))
    for a, b in zip(lo, lo[1:]):
        if close[b] < close[a] and r[b] > r[a] and not np.isnan(r[a]):
            out.append(("bullish", b))
    return sorted(out, key=lambda x: x[1])


def infer_intraday(dates):
    d = pd.to_datetime(pd.Series(dates), errors="coerce").dropna()
    if len(d) < 3:
        return False
    return d.diff().dropna().median() < pd.Timedelta(hours=20)


def analyze(df, period=14, market_cap=None, avg_volume=None, catalyst="unknown", div_window=60):
    flags = []
    if "date" in df and infer_intraday(df["date"]):
        return {"status": "REJECTED", "reason": "Intraday bars detected. RSI is unreliable on 5-10 minute charts; use daily or weekly."}
    if len(df) < 120:
        return {"status": "REJECTED", "reason": f"Only {len(df)} bars; need at least 120 for a reliable RSI."}
    close = df["close"].astype(float).reset_index(drop=True)
    last = float(close.iloc[-1])
    if last < 5:
        return {"status": "REJECTED", "reason": f"Price ${last:.2f} < $5: penny-stock territory, RSI misleads."}
    if market_cap is not None and market_cap < 3e8:
        return {"status": "REJECTED", "reason": "Market cap under $300M: too small for a reliable RSI."}
    if avg_volume is not None and avg_volume < 5e5:
        return {"status": "REJECTED", "reason": "Average volume under 500k shares: illiquid, RSI misleads."}
    if market_cap is None or avg_volume is None:
        flags.append("market cap / volume not provided: confirm the stock is not a small or illiquid name")
    ret = close.pct_change().dropna()
    if ret.abs().max() > 0.15 or (ret.abs() > 4 * ret.std()).sum() >= 3:
        flags.append("sharp price jumps in the window: RSI may be distorted")
    r = rsi(close, period)
    v = float(r.iloc[-1])
    prev = float(r.iloc[-2])
    zone = "oversold" if v < 30 else "overbought" if v > 70 else "neutral"
    if v < 30:
        signal = "BUY candidate (oversold, RSI < 30)"
    elif prev <= 70 < v:
        signal = "SELL candidate (RSI just crossed above 70)"
    elif v > 70:
        signal = "Overbought (already above 70; no fresh cross)"
    else:
        signal = "No RSI signal"
    divs = [d for d in divergences(close, r) if d[1] >= len(close) - div_window]
    bear = [i for t, i in divs if t == "bearish"]
    bull = [i for t, i in divs if t == "bullish"]
    div_note = "none recently"
    if len(bear) >= 2:
        div_note = f"{len(bear)} bearish divergences in last {div_window} bars: strong trend, DO NOT sell/short on divergence alone"
    elif bear:
        div_note = "1 bearish divergence: momentum fading, wait for confirmation"
    elif bull:
        div_note = f"{len(bull)} bullish divergence(s): momentum may be turning up, wait for confirmation"
    if catalyst == "yes":
        signal += " [NOT ORGANIC: catalyst in play, do not act]"
    elif catalyst == "unknown":
        flags.append("catalyst/sentiment not checked: run the news and sentiment check before acting")
    return {"status": "OK", "price": round(last, 2), "rsi": round(v, 1), "zone": zone,
            "hayden_regime": hayden_regime(v), "signal": signal, "divergence": div_note,
            "needs_confirmation": "yes: pair with trend-identification / mean-reversion / trend-following before acting",
            "flags": flags}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--period", type=int, default=14)
    ap.add_argument("--market-cap", type=float)
    ap.add_argument("--avg-volume", type=float)
    ap.add_argument("--catalyst", choices=["yes", "no", "unknown"], default="unknown")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    df.columns = [c.strip().lower() for c in df.columns]
    for k, v in analyze(df, a.period, a.market_cap, a.avg_volume, a.catalyst).items():
        print(f"{k}: {v}")
