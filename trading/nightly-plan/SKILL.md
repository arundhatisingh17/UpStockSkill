---
name: nightly-plan
description: Part of the trading skill. Nightly workflow that reads her Schwab positions and daily prices through the API (read-only), runs all the signal skills, and produces an order sheet plus a thinkScript study of entry/stop/target levels and alerts for her to review and use the next day. Use when she says "nightly plan", "what should I trade tomorrow", "generate my thinkScript", or "review my positions".
---

# Nightly plan (positions + signals -> order sheet + thinkScript)

**Read-only. Never place, change or cancel orders, and never handle her credentials.** thinkScript cannot place orders at all: it draws levels and fires alerts. She enters every order herself after reviewing the sheet.

## What it does
1. **Read** her positions and account value, and daily price history for the watchlist plus every held symbol (Schwab API via `schwab-py`, read-only calls only). Fallback: a folder of `TICKER.csv` files.
2. **Run the signal skills** on each symbol: trend-identification (Dow), trend-following, mean-reversion, RSI, Bollinger Bands, pivot points. Any symbol with a breakout path (Bollinger, 20-day high, pivot breakout) or that simply closed above its prior 20-day high also gets the `breakout` quality tests (big candle, fresh cross, no upper wick, volume) and the smooth-chart filter. These appear as a **flag** in the notes and the Discord digest ("GENUINE 4/4" or "2/4, failed no_wick, volume"); they do not block or create a candidate yet.
3. **Decide per symbol** using the portfolio rules:
   - Held + an exit signal (Dow SELL/STOP, trend-following exit) -> `REVIEW EXIT`.
   - Held, no exit -> `HOLD` with an ATR stop.
   - Not held + a valid entry path -> `BUY CANDIDATE` with limit price, stop, shares, and dollars at risk (1% risk per trade, 5% position cap).
   - Mean-reversion and breakout signals on the same stock -> conflict, `NO TRADE`.
4. **Write** `~/Desktop/paper-trading/plans/<date>/report.md` (order sheet and per-symbol notes) and `NightlyPlan.ts` (one thinkScript study).

## Her routine
- **Night**: ask Claude to run the nightly plan (or run `python3 nightly_plan.py --watchlist AAPL,MSFT`), then read `report.md`. Do the manual checks the script cannot: news/sentiment catalyst, earnings dates, anything that changed after the close.
- **Next day**: in thinkorswim, paste `NightlyPlan.ts` once (Charts > Studies > Edit Studies > Create), flip through the watchlist to see each symbol's entry, stop and target lines and get alerts. Enter approved BUYs as **limit orders** and set the stop as a conditional/bracket order. Confirm the order dialog.
- Log every trade (taken or skipped) in the paper ledger with `Signal source` = `nightly-plan`.

## Phone alerts
The report ends with an "Alerts to set" table (BUY alert at the entry price, SELL alert at the stop). She creates them as price alerts in the thinkorswim/Schwab mobile app so they push to her phone; the API cannot create alerts, and study alerts from the thinkScript are desktop-only as far as is known. Verify with a test alert and say plainly if delivery is uncertain. She then enters the trade herself on her phone.

**Discord digest:** `--notify` sends a one-embed summary of BUY CANDIDATE / REVIEW EXIT / HOLD rows to the team's Discord channel using the shared module `../notify/notify.py`. This covers the night-time digest only; intraday price triggers still come from the broker app alerts above. If `notify/` is not installed next to `trading/` or `DISCORD_WEBHOOK_URL` is unset, the script prints a line and still writes the report.
- The webhook URL is a secret. It lives only in `DISCORD_WEBHOOK_URL` in her shell profile. Never print it, paste it in chat, or commit it. If it leaks, delete the webhook in Discord (channel settings > Integrations > Webhooks) and create a new one.
- The webhook can only post into one channel; it cannot read anything. Send only when she asks or runs with `--notify`.

## Setup (she does this, not Claude)
- Register a Schwab developer app (market data + read-only accounts), then `pip install schwab-py pandas numpy`.
- Create the token file once with schwab-py's login flow, and set env vars `SCHWAB_APP_KEY`, `SCHWAB_APP_SECRET`, `SCHWAB_TOKEN_PATH`. Never paste them in chat or commit them. The refresh token expires after about 7 days, so she logs in again weekly.
- Claude never sees the secrets. If the API call fails, ask her for the error text only.

## Honesty about status
- The Schwab calls in `load_schwab` are **untested against the live API** (no credentials yet); expect small fixes on the first run. The CSV mode and signal pipeline are tested on synthetic data only.
- The thinkScript is **untested in thinkorswim**. Paste it, check for errors, test in paperMoney, and fix with Claude if it complains.
- Signals are analysis, not advice. The sheet never replaces her judgment. If any skill errors or data looks stale, say so rather than forcing a signal.
