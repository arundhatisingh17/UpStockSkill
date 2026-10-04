"""Mean-reversion signals for one stock. Analysis only; places no orders. Needs only numpy/pandas.

Usage: python3 mean_reversion.py prices.csv [--lookback 20]
CSV columns: date, close (case-insensitive).

Steps:
  1. Does the stock revert at all?  Hurst < 0.5 and half-life is a sane number of days.
  2. How stretched is it?           z = (price - rolling mean) / rolling std
  3. Action (long only):            z < -2 buy, z back to 0 exit, z < -3 stop (reversion failed)
"""
import argparse
import numpy as np
import pandas as pd


def hurst(x):
    """Hurst exponent from how the spread of lagged differences grows. <0.5 reverting, >0.5 trending."""
    x = np.asarray(x, dtype=float)
    lags = range(2, 40)
    tau = [np.std(x[l:] - x[:-l]) for l in lags]
    return float(np.polyfit(np.log(list(lags)), np.log(tau), 1)[0])


def half_life(x):
    """Days for a deviation to halve (AR(1) fit). Returns None if the series does not revert."""
    x = np.asarray(x, dtype=float)
    y, lag = np.diff(x), x[:-1]
    beta = np.polyfit(lag - lag.mean(), y, 1)[0]
    if beta >= 0:
        return None
    return float(-np.log(2) / np.log(1 + beta))


def variance_ratio(x, q=5):
    r = np.diff(np.log(np.asarray(x, dtype=float)))
    rq = np.diff(np.log(np.asarray(x, dtype=float)[::q]))
    return float(np.var(rq) / (q * np.var(r)))


def analyze(close, lookback=20, entry_z=2.0, stop_z=3.0):
    s = pd.Series(close, dtype=float)
    h, hl, vr = hurst(s.values), half_life(s.values), variance_ratio(s.values)
    mean, std = s.rolling(lookback).mean(), s.rolling(lookback).std()
    z = float(((s - mean) / std).iloc[-1])
    reverts = h < 0.5 and hl is not None and 2 <= hl <= 60
    if not reverts:
        action = "Do not use mean reversion (stock does not look mean-reverting; it may be trending)"
    elif z <= -stop_z:
        action = "STOP / avoid (z below -3: reversion failing)"
    elif z <= -entry_z:
        action = "BUY signal (price well below its average)"
    elif z >= entry_z:
        action = "Overextended above average: no long entry; exit any long"
    elif abs(z) < 0.25:
        action = "At the mean: exit any long"
    else:
        action = "No signal"
    return {"hurst": round(h, 2), "half_life_days": None if hl is None else round(hl, 1),
            "variance_ratio": round(vr, 2), "z_score": round(z, 2),
            "mean_reverting": reverts, "action": action,
            "target_exit": round(float(mean.iloc[-1]), 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--lookback", type=int, default=20)
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    df.columns = [c.strip().lower() for c in df.columns]
    for k, v in analyze(df["close"].values, a.lookback).items():
        print(f"{k}: {v}")
