"""Pivot-point support/resistance + pullback/breakout setups. Analysis only; places no orders.

Usage: python3 pivot_points.py prices.csv [--account 10000] [--risk 0.01]
CSV columns: date, open, high, low, close (open optional). DAILY bars.

Levels (classic), from the PREVIOUS completed period:
  PP = (H+L+C)/3   S1 = 2PP-H   S2 = PP-(H-L)   S3 = L-2(H-PP)
                   R1 = 2PP-L   R2 = PP+(H-L)   R3 = H+2(PP-L)
Setups (long only, uptrend only; pivots are NEVER a trigger on their own):
  PULLBACK : strong uptrend, the day's low dipped to a support level (PP/S1/S2) and the close held above it
  BREAKOUT : strong uptrend, close crossed above R1 (or R2) from below
  Stop     : below the support (or the broken resistance), minus 0.5 x ATR
  Exit     : sell ~half at the first resistance paying >= 1.5x the risk; trail the rest at a support >= 1 ATR below price
  Skip     : if no resistance leaves 1.5x reward-to-risk, there is no trade
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent


def _mod(rel, name):
    spec = importlib.util.spec_from_file_location(name, HERE / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pivots(h, l, c):
    pp = (h + l + c) / 3
    return {"S3": l - 2 * (h - pp), "S2": pp - (h - l), "S1": 2 * pp - h, "PP": pp,
            "R1": 2 * pp - l, "R2": pp + (h - l), "R3": h + 2 * (pp - l)}


def weekly_levels(df):
    """Pivots from the last COMPLETED calendar week (wider, better for swing holds)."""
    d = df.copy()
    d["dt"] = pd.to_datetime(d["date"])
    w = d.set_index("dt").resample("W-FRI").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    if len(w) < 2:
        return None
    last_full = w.iloc[-2] if d["dt"].iloc[-1] < w.index[-1] else w.iloc[-1]
    return pivots(last_full.high, last_full.low, last_full.close)


def atr14(df):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])


def analyze(df, account=10000.0, risk=0.01, tol=0.01):
    df = df.reset_index(drop=True)
    if len(df) < 60:
        return {"status": "REJECTED", "reason": "Need at least 60 daily bars."}
    prev, last = df.iloc[-2], df.iloc[-1]
    lv_used = pivots(prev.high, prev.low, prev.close)    # levels that applied to the last session
    lv_next = pivots(last.high, last.low, last.close)    # levels for the NEXT session
    wk = weekly_levels(df)
    close, atr = float(last.close), atr14(df)

    TD = _mod("trend-identification/trend_detector.py", "td_p")
    TF = _mod("trend-following/trend_following.py", "tf_p")
    trend, _ = TD.analyze(df.tail(250), n=3, tol=0.01)
    tf = TF.analyze(df)
    strong_up = trend == "Uptrend" and tf["trend"] == "Uptrend" and tf["adx"] > 25
    confirms = [f"Dow trend: {trend}", f"MA trend: {tf['trend']}, ADX {tf['adx']}"]
    rsi_ok = True
    try:
        RS = _mod("rsi/rsi.py", "rs_p")
        rs = RS.analyze(df, catalyst="unknown")
        if rs.get("status") == "OK":
            rsi_ok = rs["rsi"] < 70 and "bearish divergence" not in rs["divergence"]
            confirms.append(f"RSI {rs['rsi']} ({'ok' if rsi_ok else 'overbought or fading: not a clean entry'})")
        else:
            confirms.append("RSI unavailable: " + rs["reason"])
    except Exception as e:  # keep pivot output even if RSI fails
        confirms.append(f"RSI check failed: {e}")

    setup, stop, level_name, level = "None", None, None, None
    for name in ("S2", "S1", "PP"):
        lvl = lv_used[name]
        if last.low <= lvl * (1 + tol) and close > lvl and last.low >= lvl * (1 - 0.03):
            setup, level_name, level = "PULLBACK to support", name, lvl
    if setup == "None":
        for name in ("R2", "R1"):
            lvl = lv_used[name]
            if close > lvl >= prev.close:
                setup, level_name, level = "BREAKOUT above resistance", name, lvl
    if setup != "None":
        stop = level - 0.5 * atr
    bias = "above R1: upward bias" if close > lv_used["R1"] else "below S1: downward bias" if close < lv_used["S1"] \
        else "between S1 and R1: range"

    pool = {k: v for k, v in lv_next.items() if k.startswith("R")}
    if wk:
        pool.update({"W" + k: v for k, v in wk.items() if k.startswith("R")})
    above = sorted((v, k) for k, v in pool.items() if v > close * 1.005)
    # first resistance that pays at least 1.5x the risk; closer ones are skipped
    risk_ps = (close - stop) if stop is not None else None
    target = next(((v, k) for v, k in above if risk_ps and (v - close) >= 1.5 * risk_ps), None)
    # trailing support must sit at least 1 ATR below price, else it would stop out immediately
    trail = max([v for v in lv_next.values() if v < close - atr], default=None)

    out = {"status": "OK", "close": round(close, 2), "bias_vs_last_levels": bias,
           "levels_next_session": {k: round(v, 2) for k, v in lv_next.items()},
           "weekly_levels": None if not wk else {k: round(v, 2) for k, v in wk.items()},
           "strong_uptrend": strong_up, "confirmations": confirms, "setup": setup}
    if setup != "None" and strong_up and rsi_ok and target is None:
        out["decision"] = f"{setup} confirmed but no resistance gives 1.5x reward-to-risk: skip (not enough room)"
    elif setup != "None" and strong_up and rsi_ok:
        per = close - stop
        shares = int(account * risk / per) if per > 0 else 0
        out.update({"decision": f"LONG CANDIDATE ({setup}, {level_name} {level:.2f})",
                    "entry_limit": round(close, 2), "stop": round(stop, 2), "shares": shares,
                    "exit_half_at": None if target is None else f"{target[1]} {target[0]:.2f}",
                    "trail_rest_at_support": round(max(trail, stop), 2) if trail is not None else round(stop, 2),
                    "risk_pct": round(per / close * 100, 1)})
    elif setup != "None":
        out["decision"] = f"{setup} seen but NOT confirmed (trend not strong/up or RSI not clean): no trade"
    else:
        out["decision"] = "No pivot setup" + ("" if strong_up else "; trend not a strong uptrend")
    out["warnings"] = ["Pivots come from past data: run the overnight news/sentiment check before acting",
                       "Pivots are context, not triggers: need the trend and RSI confirmations above",
                       "Levels reset each session; daily levels matter most for intraday, so weekly levels are shown for swing targets"]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--account", type=float, default=10000)
    ap.add_argument("--risk", type=float, default=0.01)
    a = ap.parse_args()
    d = pd.read_csv(a.csv)
    d.columns = [c.strip().lower() for c in d.columns]
    for k, v in analyze(d, a.account, a.risk).items():
        print(f"{k}: {v}")
