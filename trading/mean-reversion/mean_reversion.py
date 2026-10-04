"""Mean-reversion signals for one stock. Analysis only; places no orders. Needs only numpy/pandas.

Usage: python3 mean_reversion.py prices.csv [--lookback 20] [--mean sma|ema|wma]
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


def moving_mean(s, n, kind="sma"):
    """Rolling mean and std around SMA (equal weights), EMA (recent-heavy, exponential) or WMA (recent-heavy, linear)."""
    if kind == "ema":
        m = s.ewm(span=n, adjust=False, min_periods=n).mean()
        sd = (s - m).pow(2).ewm(span=n, adjust=False, min_periods=n).mean().pow(0.5)
    elif kind == "wma":
        w = np.arange(1, n + 1, dtype=float)
        w /= w.sum()
        m = s.rolling(n).apply(lambda x: float(np.dot(x, w)), raw=True)
        sd = (s - m).pow(2).rolling(n).mean().pow(0.5)
    else:
        m, sd = s.rolling(n).mean(), s.rolling(n).std()
    return m, sd


def zscores(s, n):
    out = {}
    for k in ("sma", "ema", "wma"):
        m, sd = moving_mean(s, n, k)
        out[k] = (float(((s - m) / sd).iloc[-1]), float(m.iloc[-1]))
    return out


def analyze(close, lookback=20, entry_z=2.0, stop_z=3.0, mean="sma"):
    s = pd.Series(close, dtype=float)
    h, hl, vr = hurst(s.values), half_life(s.values), variance_ratio(s.values)
    zs = zscores(s, lookback)
    z, mean_now = zs[mean]
    agree = sum(1 for v, _ in zs.values() if v <= -entry_z)
    reverts = h < 0.5 and hl is not None and 2 <= hl <= 60
    if not reverts:
        action = "Do not use mean reversion (stock does not look mean-reverting; it may be trending)"
    elif z <= -stop_z:
        action = "STOP / avoid (z below -3: reversion failing)"
    elif z <= -entry_z and agree >= 2:
        action = "BUY signal (price well below its average; %d of 3 averages agree)" % agree
    elif z <= -entry_z:
        action = "Weak: only %d of 3 averages agree; likely noise, skip" % agree
    elif z >= entry_z:
        action = "Overextended above average: no long entry; exit any long"
    elif abs(z) < 0.25:
        action = "At the mean: exit any long"
    else:
        action = "No signal"
    # SMA vs EMA gap: fast average far below slow one hints a trend is developing
    gap = (zs["ema"][1] - zs["sma"][1]) / zs["sma"][1] * 100
    return {"hurst": round(h, 2), "half_life_days": None if hl is None else round(hl, 1),
            "variance_ratio": round(vr, 2), "mean_used": mean,
            "z_sma": round(zs["sma"][0], 2), "z_ema": round(zs["ema"][0], 2), "z_wma": round(zs["wma"][0], 2),
            "ema_vs_sma_gap_pct": round(gap, 2),
            "trend_warning": gap < -1.5,
            "mean_reverting": reverts, "action": action, "target_exit": round(mean_now, 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--lookback", type=int, default=20)
    ap.add_argument("--mean", choices=["sma", "ema", "wma"], default="sma")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    df.columns = [c.strip().lower() for c in df.columns]
    for k, v in analyze(df["close"].values, a.lookback, mean=a.mean).items():
        print(f"{k}: {v}")
