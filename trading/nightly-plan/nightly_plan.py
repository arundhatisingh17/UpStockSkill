"""Nightly plan: positions + market data + skill signals -> order sheet + thinkScript. READ-ONLY.

This script never places, changes or cancels orders. It only reads (positions, price history)
and writes files for YOU to review and use in thinkorswim.

Usage:
  Schwab (read-only):  python3 nightly_plan.py --watchlist AAPL,MSFT,NVDA
  CSV folder / demo :  python3 nightly_plan.py --csv-dir ./prices --watchlist AAPL,MSFT [--positions-json pos.json] [--equity 10000]

Schwab auth uses env vars YOU set (never paste them into chat or commit them):
  SCHWAB_APP_KEY  SCHWAB_APP_SECRET  SCHWAB_TOKEN_PATH   (token file made once by schwab-py's login flow)
Output: ~/Desktop/paper-trading/plans/<date>/report.md and NightlyPlan.ts
Optional: --notify posts a digest to Discord through the sibling notify/ skill (webhook in env var DISCORD_WEBHOOK_URL).
"""
import argparse
import importlib.util
import json
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
RISK_PER_TRADE = 0.01
MAX_POSITION = 0.05


def load_mod(rel, name):
    spec = importlib.util.spec_from_file_location(name, HERE / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TD = load_mod("trend-identification/trend_detector.py", "td")
TF = load_mod("trend-following/trend_following.py", "tf")
MR = load_mod("mean-reversion/mean_reversion.py", "mr")
RS = load_mod("rsi/rsi.py", "rs")
BB = load_mod("bollinger-bands/bollinger.py", "bb")
PV = load_mod("pivot-points/pivot_points.py", "pv")


# ---------- data (read-only) ----------
def load_csv_dir(d, symbols):
    out = {}
    for s in symbols:
        p = Path(d) / f"{s}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df.columns = [c.strip().lower() for c in df.columns]
            out[s] = df
    return out


def load_schwab(symbols):
    """Read-only Schwab calls via schwab-py. UNTESTED against the live API: verify on first run."""
    from schwab import auth  # pip install schwab-py
    c = auth.client_from_token_file(os.environ["SCHWAB_TOKEN_PATH"], os.environ["SCHWAB_APP_KEY"],
                                    os.environ["SCHWAB_APP_SECRET"])
    acct_hash = c.get_account_numbers().json()[0]["hashValue"]
    acct = c.get_account(acct_hash, fields=[c.Account.Fields.POSITIONS]).json()["securitiesAccount"]
    equity = float(acct["currentBalances"].get("liquidationValue", 0))
    positions = {p["instrument"]["symbol"]: {"qty": p["longQuantity"] - p.get("shortQuantity", 0),
                                              "avg": p.get("averagePrice", 0)}
                 for p in acct.get("positions", []) if p["instrument"].get("assetType") == "EQUITY"}
    data = {}
    for s in sorted(set(symbols) | set(positions)):
        r = c.get_price_history_every_day(s, need_extended_hours_data=False).json()
        df = pd.DataFrame(r.get("candles", []))
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["datetime"], unit="ms").dt.strftime("%Y-%m-%d")
        data[s] = df[["date", "open", "high", "low", "close", "volume"]]
    return data, positions, equity


# ---------- signals ----------
def evaluate(sym, df, held):
    df = df.reset_index(drop=True)
    last = df.iloc[-1]
    close = float(last["close"])
    trend, events = TD.analyze(df.tail(250), n=3, tol=0.01)
    dow_event = events[-1] if events and str(events[-1][0]) == str(last["date"]) else None
    tf = TF.analyze(df)
    mr = MR.analyze(df["close"].values)
    rs = RS.analyze(df, catalyst="unknown")
    bb = BB.analyze(df)
    pv = PV.analyze(df)
    notes = []

    exits = []
    if dow_event and dow_event[1] in ("SELL", "STOP"):
        exits.append(f"Dow Theory {dow_event[1]}: {dow_event[3]}")
    if tf["action"].startswith("EXIT"):
        exits.append("Trend following exit: " + tf["action"])
    if held and "At the mean" in mr["action"]:
        notes.append("Mean reversion: price back at the average (exit if this was a dip trade)")

    paths = []
    if tf["suggests"] == "trend following" and tf["action"].startswith("ENTRY") and trend == "Uptrend":
        paths.append(("Trend following + Dow uptrend", tf["atr_stop"]))
    if dow_event and dow_event[1] == "BUY" and tf["trend_strength"] != "none":
        paths.append(("Dow Theory higher-low/higher-high", tf["atr_stop"]))
    if mr["mean_reverting"] and mr["action"].startswith("BUY") and tf["trend_strength"] != "strong":
        sd = df["close"].tail(20).std()
        paths.append(("Mean reversion (z <= -2, 2+ averages agree)", round(mr["target_exit"] - 3 * sd, 2)))
    if bb.get("status") == "OK" and bb["action"].startswith("BREAKOUT ENTRY") and "SIDEWAYS" not in bb["action"]:
        paths.append(("Bollinger breakout", round(float(last["low"]), 2)))

    if pv.get("decision", "").startswith("LONG"):
        paths.insert(0, ("Pivot " + pv["setup"].split()[0].lower(), pv["stop"]))
    kinds = {p[0].split()[0] for p in paths}
    conflict = "Mean" in kinds and ("Bollinger" in kinds or "Trend" in kinds)
    if rs.get("status") == "REJECTED":
        notes.append("RSI unavailable: " + rs["reason"])
    else:
        notes.append(f"RSI {rs['rsi']} ({rs['zone']}); {rs['divergence']}")
        if rs["divergence"].startswith("2 bearish") or "DO NOT sell" in rs["divergence"]:
            notes.append("Repeated bearish divergences: not a reason to sell on its own")
    notes.append("Catalyst/news check NOT done: search the news before acting")
    notes.append("Earnings date NOT checked: skip if earnings are within a few days")

    decision, why, stop = "HOLD" if held else "NO TRADE", "", None
    if held and exits:
        decision, why = "REVIEW EXIT", "; ".join(exits)
    elif held:
        decision = "HOLD"
        stop = tf["atr_stop"]
    elif conflict:
        decision, why = "NO TRADE", "mean-reversion and breakout signals conflict: skipped"
    elif paths:
        decision, why, stop = "BUY CANDIDATE", " + ".join(p[0] for p in paths), paths[0][1]
    return {"sym": sym, "close": close, "trend": trend, "adx": tf["adx"], "decision": decision, "why": why,
            "stop": stop, "paths": len(paths), "mr_target": mr["target_exit"], "pv": pv, "notes": notes,
            "date": str(last["date"])}


def size(equity, entry, stop):
    per_share = entry - stop
    if per_share <= 0 or equity <= 0:
        return 0, 0.0
    shares = int(min(equity * RISK_PER_TRADE / per_share, equity * MAX_POSITION / entry))
    return shares, round(shares * per_share, 2)


# ---------- outputs ----------
def thinkscript(rows):
    """One study: paste once, flip through the watchlist; each chart shows its own levels and alerts."""
    def pick(field):
        expr = "Double.NaN"
        for r in reversed(rows):
            if r[field] is not None:
                expr = f'if GetSymbol() == "{r["sym"]}" then {r[field]} else {expr}'
        return expr
    lines = [f"# NightlyPlan generated {date.today()} - REVIEW BEFORE USE. Draws levels and alerts only; it cannot place orders.",
             "# Paste into: Charts > Studies > Edit Studies > Create. Test in paperMoney first.",
             f"def entry = {pick('entry')};", f"def stop = {pick('stop')};", f"def target = {pick('target')};",
             "plot Entry = entry;", "plot Stop = stop;", "plot Target = target;",
             "Entry.SetDefaultColor(Color.GREEN);", "Stop.SetDefaultColor(Color.RED);", "Target.SetDefaultColor(Color.CYAN);",
             'Entry.SetPaintingStrategy(PaintingStrategy.DASHES);', 'Stop.SetPaintingStrategy(PaintingStrategy.DASHES);',
             'Alert(!IsNaN(entry) and AbsValue(close - entry) / entry < 0.005, "Price near your planned entry: review before acting", Alert.ONCE, Sound.Ding);',
             'Alert(!IsNaN(stop) and close <= stop, "STOP level hit: review your position", Alert.ONCE, Sound.Ring);',
             'AddLabel(!IsNaN(entry) or !IsNaN(stop), "Plan: entry " + entry + " | stop " + stop, Color.YELLOW);']
    return "\n".join(lines) + "\n"


def digest(rows, report_path):
    """(title, lines, color) for notify.send(): anything actionable, then what is held."""
    color = {"BUY CANDIDATE": 0x0F6B4F, "REVIEW EXIT": 0xA2461C}
    act = [r for r in rows if r["decision"] in color]
    lines = []
    for r in act:
        if r["decision"] == "BUY CANDIDATE":
            lines.append(f"**{r['sym']}** BUY CANDIDATE: limit {r['entry']}, stop {r['stop']}, "
                         f"{r['shares'] or 0} sh (${r['risk'] or 0} at risk). {r['why']}")
        else:
            lines.append(f"**{r['sym']}** REVIEW EXIT: {r['why']}")
    held = [r["sym"] for r in rows if r["decision"] == "HOLD"]
    if held:
        lines.append("Holding: " + ", ".join(held))
    lines.append(("\n" if lines else "") + f"Analysis only, nothing was ordered. Full sheet: `{report_path}`")
    title = f"Nightly plan {date.today()}: {len(act)} to review" if act else f"Nightly plan {date.today()}: no trades"
    return title, lines, color[act[0]["decision"]] if act else 0x6B6B63


def send_notification(rows, report_path):
    """notify/ is a shared module installed next to trading/; a missing copy must never break the plan."""
    path = HERE.parent / "notify" / "notify.py"
    if not path.exists():
        print(f"--notify: notify module not found at {path} (copy notify/ next to trading/), skipped")
        return
    spec = importlib.util.spec_from_file_location("notify", path)
    nt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nt)
    nt.send(*digest(rows, report_path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watchlist", default="")
    ap.add_argument("--csv-dir")
    ap.add_argument("--positions-json")
    ap.add_argument("--equity", type=float, default=10000)
    ap.add_argument("--out", default=str(Path.home() / "Desktop/paper-trading/plans"))
    ap.add_argument("--notify", action="store_true", help="post a digest to Discord via notify/notify.py")
    a = ap.parse_args()
    symbols = [s.strip().upper() for s in a.watchlist.split(",") if s.strip()]
    if a.csv_dir:
        positions = json.load(open(a.positions_json)) if a.positions_json else {}
        data, equity = load_csv_dir(a.csv_dir, sorted(set(symbols) | set(positions))), a.equity
    else:
        data, positions, equity = load_schwab(symbols)

    rows = []
    for sym, df in data.items():
        r = evaluate(sym, df, sym in positions)
        r["entry"], r["target"], r["shares"], r["risk"] = None, None, 0, 0.0
        if r["decision"] == "BUY CANDIDATE" and r["stop"]:
            r["entry"] = round(r["close"], 2)
            r["shares"], r["risk"] = size(equity, r["entry"], r["stop"])
            r["target"] = round(r["mr_target"], 2) if "Mean" in r["why"] else None
            if "Pivot" in r["why"] and r["pv"].get("exit_half_at"):
                r["target"] = float(r["pv"]["exit_half_at"].split()[1])
                r["notes"].append(f"Pivot plan: sell about half at {r['pv']['exit_half_at']}, trail the rest at {r['pv']['trail_rest_at_support']} (raise it to each new support as price climbs)")
        if r["sym"] in positions:
            p = positions[r["sym"]]
            r["held"] = f"{p['qty']} sh @ {p['avg']} ({(r['close'] / p['avg'] - 1) * 100:+.1f}%)" if p.get("avg") else f"{p['qty']} sh"
        rows.append(r)

    out = Path(a.out) / str(date.today())
    out.mkdir(parents=True, exist_ok=True)
    md = [f"# Nightly plan {date.today()}", f"Equity used: ${equity:,.0f}. Risk {RISK_PER_TRADE:.0%}/trade, cap {MAX_POSITION:.0%}/position.",
          "Analysis only, not investment advice. Review every line yourself. Nothing was ordered.", "",
          "| Symbol | Close | Trend | ADX | Decision | Why | Entry (limit) | Stop | Shares | $ at risk | Held |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['sym']} | {r['close']:.2f} | {r['trend']} | {r['adx']} | **{r['decision']}** | {r['why'] or '-'} | "
                  f"{r['entry'] or '-'} | {r['stop'] if r['stop'] else '-'} | {r['shares'] or '-'} | {r['risk'] or '-'} | {r.get('held', '-')} |")
    alerts = []
    for r in rows:
        if r["decision"] == "BUY CANDIDATE" and r["entry"]:
            alerts.append(f"| {r['sym']} | BUY alert | Price at or below {r['entry']} | Then enter limit buy {r['shares']} sh, stop {r['stop']} |")
        if r["decision"] == "HOLD" and r["stop"]:
            alerts.append(f"| {r['sym']} | SELL alert (stop) | Price at or below {round(r['stop'], 2)} | Review and sell if the thesis is broken |")
        if r["decision"] == "REVIEW EXIT":
            alerts.append(f"| {r['sym']} | SELL review | Open the position at the next open | {r['why']} |")
    md += ["", "## Alerts to set (for phone push notifications)",
           "Create these as price alerts in the thinkorswim or Schwab mobile app so they push to your phone, and send yourself a test alert first to confirm it arrives. "
           "The thinkScript study alerts run on the desktop; do not count on them reaching your phone.",
           "| Symbol | Type | Condition | Then |", "|---|---|---|---|"] + (alerts or ["| - | - | - | none today |"])
    md += ["", "## Notes per symbol"]
    for r in rows:
        md.append(f"**{r['sym']}**: " + " | ".join(r["notes"]))
    md += ["", "## Before you enter anything",
           "- Check the news and earnings date for each symbol (not automated).",
           "- Enter BUYs as limit orders; set the stop as a conditional/bracket order immediately.",
           "- Confirm account, symbol, quantity and limit price in thinkorswim's confirmation dialog.",
           "- Log each trade (taken or skipped) in the paper ledger."]
    (out / "report.md").write_text("\n".join(md) + "\n")
    (out / "NightlyPlan.ts").write_text(thinkscript(rows))
    print("Wrote", out / "report.md", "and", out / "NightlyPlan.ts")
    print("\n".join(md[5:5 + len(rows) + 2]))
    if a.notify:
        send_notification(rows, out / "report.md")


if __name__ == "__main__":
    main()
