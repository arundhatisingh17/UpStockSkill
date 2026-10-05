"""Breakout quality: is this a genuine breakout candle or a false one? Analysis only; places no orders.

Usage: python3 breakout.py prices.csv [--level 123.45] [--account 10000] [--risk 0.01]
CSV columns: date, high, low, close, plus open and volume if you have them (two of the four tests need them).

Four tests on the breakout candle (the daily bar that closed above the level):
  big       range >= 1.5 x ATR(14)                 the bar is larger than this stock's normal day
  fresh     close > level and the 3 prior closes were not   a fresh cross, not a stock already running above
  no_wick   (high - close) / range < 20%          closed near the high: sellers did not push it back
  volume    volume >= 1.5 x 20-day average        someone big was buying (unknown without a volume column)
Chart filter (whole lookback, not one bar):
  smooth    few gaps (|open - prev close| > 3%) and short upper wicks on average; gappy/wicky charts are rejected

Execution plan this skill prints (from the book; the nightly plan does NOT apply it yet, it only shows the flags):
  entry     buy-stop a few ticks above the breakout candle high; skip if it opens > 2% above that high
  stop      a few ticks below the breakout candle low
  trail     if the next day's candle is small or red, raise the stop to that day's low
  exit      75% at target, trail the remaining 25% under swing lows
"""
import argparse
import numpy as np
import pandas as pd

ATR_MULT = 1.5
WICK_MAX = 0.20
VOL_MULT = 1.5
GAP_PCT = 0.03
MAX_GAPS = 6
MAX_MEAN_WICK = 0.45   # a normal daily bar carries ~25-30% upper wick on average; 45%+ is chronically wicky
GAP_SKIP = 0.02
TICK = 0.01


def atr(df, n=14):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _upper_wick_ratio(df):
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    top = df[["open", "close"]].max(axis=1) if "open" in df else df["close"]
    return ((df["high"] - top) / rng).clip(lower=0)


def smooth(df, lookback=120):
    """Is the chart tradeable at all? Gappy or chronically wicky price action trips stops and entries at random."""
    d = df.tail(lookback).reset_index(drop=True)
    wick = float(_upper_wick_ratio(d).mean())
    gaps = None
    if "open" in d:
        gaps = int(((d["open"] - d["close"].shift(1)).abs() / d["close"].shift(1) > GAP_PCT).sum())
    reasons = []
    if gaps is not None and gaps > MAX_GAPS:
        reasons.append(f"{gaps} gaps over 3% in {len(d)} bars")
    if wick > MAX_MEAN_WICK:
        reasons.append(f"average upper wick {wick:.0%} of range")
    return {"ok": not reasons, "gaps_over_3pct": gaps, "mean_upper_wick": round(wick, 2),
            "reason": "; ".join(reasons) or "smooth enough", "gaps_known": gaps is not None}


def quality(df, level=None, i=-1):
    """Score the candle at index i against the four tests. level defaults to the prior 20-day high."""
    d = df.reset_index(drop=True)
    i = i % len(d)
    if i < 25:
        return {"status": "REJECTED", "reason": f"need 25+ bars before the candle, have {i}"}
    bar, prev = d.iloc[i], d.iloc[i - 1]
    rng = float(bar["high"] - bar["low"])
    if rng <= 0:
        return {"status": "REJECTED", "reason": "zero-range candle"}
    if level is None:
        level = float(d["high"].iloc[i - 20:i].max())
    a = float(atr(d.iloc[: i + 1]).iloc[-1])
    prior_closes = d["close"].iloc[i - 3:i]

    tests = {
        "big": (rng >= ATR_MULT * a, f"range {rng / a:.1f}x ATR"),
        "fresh": (bar["close"] > level and bool((prior_closes <= level).all()),
                  "fresh cross" if bar["close"] > level and (prior_closes <= level).all()
                  else "not above level" if bar["close"] <= level else "already above level before today"),
        "no_wick": ((bar["high"] - bar["close"]) / rng < WICK_MAX, f"upper wick {(bar['high'] - bar['close']) / rng:.0%}"),
    }
    if "volume" in d and pd.notna(bar.get("volume")) and i >= 21:
        avg = float(d["volume"].iloc[i - 20:i].mean())
        ratio = float(bar["volume"]) / avg if avg > 0 else float("nan")
        tests["volume"] = (bool(ratio >= VOL_MULT), f"volume {ratio:.1f}x 20-day avg")
    else:
        tests["volume"] = (None, "volume unknown (no volume column)")

    known = {k: v for k, v in tests.items() if v[0] is not None}
    passed = [k for k, v in known.items() if v[0]]
    failed = [k for k, v in known.items() if not v[0]]
    genuine = not failed and len(known) == 4
    detail = "; ".join(f"{k}: {v[1]}" for k, v in tests.items())
    summary = f"{len(passed)}/{len(known)} tests" + (f", failed {', '.join(failed)}" if failed else "")
    if tests["volume"][0] is None:
        summary += " (volume unknown)"
    return {"status": "OK", "level": round(float(level), 2), "atr": round(a, 2), "genuine": genuine,
            "score": len(passed), "known": len(known), "passed": passed, "failed": failed,
            "summary": summary, "detail": detail, "tests": {k: v[0] for k, v in tests.items()},
            "high": round(float(bar["high"]), 2), "low": round(float(bar["low"]), 2), "close": round(float(bar["close"]), 2)}


def plan(q, account=10000.0, risk=0.01):
    """The book's execution plan for a candle that passed. Informational; the nightly plan does not apply it yet."""
    entry = round(q["high"] + TICK, 2)
    stop = round(q["low"] - TICK, 2)
    per_share = entry - stop
    shares = int(account * risk / per_share) if per_share > 0 else 0
    return {"entry_buy_stop": entry, "stop": stop, "skip_if_open_above": round(q["high"] * (1 + GAP_SKIP), 2),
            "risk_per_share": round(per_share, 2), "shares_at_risk_pct": shares,
            "min_target_for_1to2": round(entry + 2 * per_share, 2),
            "day_after": "if the next candle is small or red, raise the stop to that day's low",
            "exit": "75% at target, trail the remaining 25% below swing lows"}


def analyze(df, level=None, account=10000.0, risk=0.01):
    sm = smooth(df)
    q = quality(df, level=level)
    out = {"smooth": sm, "quality": q}
    if q.get("status") == "OK" and q["score"] == q["known"] and sm["ok"]:
        out["plan"] = plan(q, account, risk)
    return out


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--level", type=float, help="breakout level (default: prior 20-day high)")
    ap.add_argument("--account", type=float, default=10000)
    ap.add_argument("--risk", type=float, default=0.01)
    a = ap.parse_args()
    r = analyze(load(a.csv), a.level, a.account, a.risk)
    print("Chart :", r["smooth"]["reason"], f"(gaps>3%: {r['smooth']['gaps_over_3pct']}, mean upper wick {r['smooth']['mean_upper_wick']})")
    q = r["quality"]
    if q.get("status") != "OK":
        print("Candle:", q["reason"])
    else:
        print(f"Candle: level {q['level']} | {q['summary']} | genuine={q['genuine']}")
        print("        " + q["detail"])
    if "plan" in r:
        p = r["plan"]
        print(f"Plan  : buy-stop {p['entry_buy_stop']} (skip if open > {p['skip_if_open_above']}), stop {p['stop']}, "
              f"{p['shares_at_risk_pct']} sh at {a.risk:.0%} risk, target must be >= {p['min_target_for_1to2']} for 1:2")
        print("        " + p["day_after"] + "; " + p["exit"])
    else:
        print("Plan  : none (not every test passed, or chart not smooth). Analysis only, not advice.")
