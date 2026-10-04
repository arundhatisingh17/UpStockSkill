"""Dow Theory swing-structure trend detector. Analysis only; places no orders.

Usage:
    python3 trend_detector.py prices.csv [--n 3] [--tol 0.01]
CSV needs columns: date, high, low, close (case-insensitive). Optional: import and call analyze(df).

Rules (closing-price confirmation, user's spec):
  Uptrend    : higher highs + higher lows
  Downtrend  : lower highs  + lower lows
  Sideways   : highs and lows within `tol` of the previous ones
  Mixed      : anything else (transition, wait)
  SELL       : in an uptrend, a lower high forms, then a CLOSE below the last swing low
  BUY        : after a downtrend, a higher low forms, then a CLOSE above the last swing high;
               stop-loss = that higher low
"""
import argparse
import pandas as pd


def swings(df, n):
    """Swing high/low = extreme over n bars each side. Confirmed n bars after the fact."""
    out = []
    for i in range(n, len(df) - n):
        win = df.iloc[i - n:i + n + 1]
        if df["high"].iloc[i] == win["high"].max():
            out.append((i, "H", df["high"].iloc[i]))
        if df["low"].iloc[i] == win["low"].min():
            out.append((i, "L", df["low"].iloc[i]))
    # collapse consecutive same-type swings, keeping the more extreme
    clean = []
    for p in sorted(out, key=lambda x: x[0]):
        if clean and clean[-1][1] == p[1]:
            keep_new = p[2] > clean[-1][2] if p[1] == "H" else p[2] < clean[-1][2]
            if keep_new:
                clean[-1] = p
        else:
            clean.append(p)
    return clean


def cmp(new, old, tol):
    if abs(new - old) <= tol * old:
        return 0
    return 1 if new > old else -1


def classify(sw, tol):
    highs = [p for p in sw if p[1] == "H"][-2:]
    lows = [p for p in sw if p[1] == "L"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "Insufficient data"
    h = cmp(highs[1][2], highs[0][2], tol)
    l = cmp(lows[1][2], lows[0][2], tol)
    if h == 1 and l == 1:
        return "Uptrend"
    if h == -1 and l == -1:
        return "Downtrend"
    if h == 0 and l == 0:
        return "Sideways"
    return "Mixed/transition"


def analyze(df, n=3, tol=0.01):
    df = df.reset_index(drop=True)
    events, trend = [], None
    in_position, last_stop = False, None
    for t in range(2 * n + 1, len(df)):
        sw = [p for p in swings(df.iloc[:t + 1], n) if p[0] <= t - n]  # confirmed only
        if len(sw) < 4:
            continue
        trend = classify(sw, tol)
        close = df["close"].iloc[t]
        highs = [p for p in sw if p[1] == "H"]
        lows = [p for p in sw if p[1] == "L"]
        if len(highs) < 2 or len(lows) < 2:
            continue
        lower_high = highs[-1][2] < highs[-2][2] * (1 - tol)
        higher_low = lows[-1][2] > lows[-2][2] * (1 + tol)
        # SELL: lower high formed, then close breaks below last swing low
        if in_position and lower_high and highs[-1][0] > lows[-1][0] and close < lows[-1][2]:
            events.append((df["date"].iloc[t], "SELL", close,
                           f"lower high {highs[-1][2]:.2f}, broke swing low {lows[-1][2]:.2f}"))
            in_position, last_stop = False, None
        # BUY: higher low formed, then close breaks above last swing high
        elif (not in_position and higher_low and lows[-1][0] > highs[-1][0]
              and close > highs[-1][2]):
            events.append((df["date"].iloc[t], "BUY", close,
                           f"higher low {lows[-1][2]:.2f} (stop-loss), broke swing high {highs[-1][2]:.2f}"))
            in_position, last_stop = True, lows[-1][2]
        # protective stop
        elif in_position and last_stop is not None and close < last_stop:
            events.append((df["date"].iloc[t], "STOP", close, f"closed below stop {last_stop:.2f}"))
            in_position, last_stop = False, None
    return trend, events


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df[["date", "high", "low", "close"]]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--n", type=int, default=3, help="bars each side for a swing")
    ap.add_argument("--tol", type=float, default=0.01, help="'same level' tolerance")
    a = ap.parse_args()
    trend, events = analyze(load(a.csv), a.n, a.tol)
    print("Current trend:", trend)
    for e in events:
        print(*e, sep=" | ")
