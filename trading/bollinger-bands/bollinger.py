"""Bollinger Band volatility-breakout signals for one stock. Analysis only; places no orders.

Usage: python3 bollinger.py prices.csv [--period 20] [--k 2] [--account 10000] [--risk 0.01]
CSV columns: date, high, low, close. DAILY or WEEKLY bars only.

Strategy (breakout, not dip-buying):
  Bands   : middle = 20-day SMA, upper/lower = middle +/- 2 standard deviations
  Squeeze : bandwidth (upper-lower)/middle in its lowest 20% of the last 120 bars = quiet, coiled market
  Entry   : close breaks ABOVE the upper band (best right after a squeeze)
  Stop    : low of the breakout candle
  Trail   : exit when the close falls below the middle band
  Sideways: ADX < 20 means breakouts are often false. Flagged and counted.
  Fit     : needs a volatile stock (annualized volatility >= 30%); calm stocks rarely break out.
"""
import argparse
import numpy as np
import pandas as pd


def bands(close, n=20, k=2.0):
    mid = close.rolling(n).mean()
    sd = close.rolling(n).std()
    return mid, mid + k * sd, mid - k * sd


def adx(df, n=14):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    a = tr.ewm(alpha=1 / n, adjust=False).mean()
    up, dn = df["high"].diff(), -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * mdm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def infer_intraday(dates):
    d = pd.to_datetime(pd.Series(dates), errors="coerce").dropna()
    return len(d) >= 3 and d.diff().dropna().median() < pd.Timedelta(hours=20)


def run(df, n=20, k=2.0, squeeze_pct=0.2, lookback=120, squeeze_window=10):
    d = df.reset_index(drop=True).copy()
    d["mid"], d["up"], d["lo"] = bands(d["close"], n, k)
    d["bw"] = (d["up"] - d["lo"]) / d["mid"]
    d["bw_rank"] = d["bw"].rolling(lookback).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    d["squeeze"] = d["bw_rank"] <= squeeze_pct
    d["recent_squeeze"] = d["squeeze"].rolling(squeeze_window, min_periods=1).max().astype(bool)
    d["adx"] = adx(d)
    trades, pos = [], None
    for i in range(lookback + n, len(d)):
        r = d.iloc[i]
        if pos is None:
            if r.close > r.up and d.iloc[i - 1].close <= d.iloc[i - 1].up:
                pos = {"i": i, "entry": r.close, "stop": r.low, "squeeze": bool(r.recent_squeeze),
                       "sideways": bool(r.adx < 20), "date": r.date}
        else:
            exit_px = None
            if r.low <= pos["stop"]:
                exit_px = min(pos["stop"], r.open if "open" in d else pos["stop"])
            elif r.close < r.mid:
                exit_px = r.close
            if exit_px is not None:
                pos.update(exit=exit_px, bars=i - pos["i"], ret=exit_px / pos["entry"] - 1)
                trades.append(pos)
                pos = None
    return d, trades, pos


def stats(trades):
    if not trades:
        return {"n": 0}
    rets = np.array([t["ret"] for t in trades])
    return {"n": len(trades), "win_rate": round(float((rets > 0).mean()), 2),
            "avg_return_pct": round(float(rets.mean() * 100), 2)}


def analyze(df, n=20, k=2.0, account=10000.0, risk=0.01):
    if "date" in df and infer_intraday(df["date"]):
        return {"status": "REJECTED", "reason": "Intraday bars detected. Use daily or weekly charts."}
    if len(df) < 200:
        return {"status": "REJECTED", "reason": f"Only {len(df)} bars; need at least 200."}
    d, trades, pos = run(df, n, k)
    last = d.iloc[-1]
    vol = float(d["close"].pct_change().std() * np.sqrt(252) * 100)
    flags = []
    if vol < 30:
        flags.append(f"annualized volatility {vol:.0f}% < 30%: calm stock, breakouts rarely follow through; poor fit")
    sideways = [t for t in trades if t["sideways"]]
    trending = [t for t in trades if not t["sideways"]]
    fresh = last.close > last.up and d.iloc[-2].close <= d.iloc[-2].up
    if pos is not None:
        action = f"IN BREAKOUT since {pos['date']}: hold; trail stop at middle band {last.mid:.2f}; initial stop {pos['stop']:.2f}"
    elif fresh:
        risk_per_share = last.close - last.low
        shares = int(account * risk / risk_per_share) if risk_per_share > 0 else 0
        action = "BREAKOUT ENTRY signal (close above upper band)"
        if last.adx < 20:
            action += " [SIDEWAYS WARNING: ADX < 20, likely false signal]"
        if not last.recent_squeeze:
            flags.append("no recent squeeze: breakout is from an already-volatile market, weaker setup")
        flags.append(f"stop at breakout-candle low {last.low:.2f} ({risk_per_share / last.close * 100:.1f}% risk); size {shares} shares at {risk:.0%} account risk")
    elif last.close < last.lo:
        action = "Below lower band: no long signal here (this strategy only buys upside breakouts)"
    else:
        action = "No signal (price inside the bands)"
    return {"status": "OK", "price": round(float(last.close), 2), "upper": round(float(last.up), 2),
            "middle": round(float(last.mid), 2), "lower": round(float(last.lo), 2),
            "bandwidth_percentile": None if np.isnan(last.bw_rank) else round(float(last.bw_rank), 2),
            "in_squeeze": bool(last.squeeze), "adx": round(float(last.adx), 1),
            "annual_vol_pct": round(vol, 0), "action": action, "flags": flags,
            "history_all": stats(trades), "history_when_sideways": stats(sideways), "history_when_trending": stats(trending)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--period", type=int, default=20)
    ap.add_argument("--k", type=float, default=2.0)
    ap.add_argument("--account", type=float, default=10000)
    ap.add_argument("--risk", type=float, default=0.01)
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    df.columns = [c.strip().lower() for c in df.columns]
    for key, v in analyze(df, a.period, a.k, a.account, a.risk).items():
        print(f"{key}: {v}")
