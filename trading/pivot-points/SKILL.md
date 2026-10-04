---
name: pivot-points
description: Part of the trading skill. Calculates pivot points (PP, S1-S3, R1-R3) from the previous period and uses them as support/resistance for pullback and breakout setups in confirmed uptrends, with stop below support, a partial exit at the next resistance, and a trailing stop. Use when she asks about support/resistance, pivot points, pullbacks, breakouts, or where to place stops and targets.
---

# Pivot points (support and resistance)

Analysis and simulated signals only; never place orders.

## Formulas (previous period's High, Low, Close)
- **PP** = (H + L + C) / 3
- **S1** = 2PP - H, **S2** = PP - (H - L), **S3** = L - 2(H - PP)
- **R1** = 2PP - L, **R2** = PP + (H - L), **R3** = H + 2(PP - L)
- Levels come from the previous completed trading day and stay the same on any chart timeframe. For swing holds the script also shows **weekly** levels (previous week), which are wider and more meaningful over days to weeks.

## How to read them
- **Support** is a price where many buyers step in; **resistance** is where many sellers do. A touch of resistance often turns price down; a touch of support often turns it up.
- If price opens **near PP**, S1 and R1 act as the first support and resistance. S2/R2 and S3/R3 mark where a move may stall or reverse.
- Open or break **above R1**: upward bias. Open or break **below S1**: downward bias. This is a bias, not a promise.

## Goal: trade only strong trends
1. **Trend**: use the other skills together to confirm a **strong uptrend**: Dow Theory uptrend (`trend-identification`), moving-average uptrend with ADX above 25 (`trend-following`). If not a strong uptrend, stop: levels are context only.
2. **Setup** (either):
   - **Pullback**: the day's low dipped to PP/S1/S2 and the close held above it.
   - **Breakout**: the close crossed above R1 (or R2) from below.
3. **Confirm**: RSI below 70 with no bearish divergence (`rsi`). Pivots are never an entry or exit by themselves.
4. **Stop-loss**: below the support (or the broken resistance, which becomes support), minus 0.5 x ATR.
5. **Exit in parts**: sell about half at the first resistance that pays at least 1.5x the risk; skip the trade if none does. Carry the rest with a **trailing stop at the support level** below price (at least 1 ATR away), raising it each time price clears a higher support.
6. Size so the stop-out costs about 1% of the account.

## Limits (state them every time)
- Pivots come from **past data**. Run the overnight news and sentiment check before acting; a gap or catalyst can invalidate every level.
- Never use pivots alone as an entry or exit signal; require the trend and RSI confirmations.
- Daily pivots reset every session and matter most for intraday trading; our swing trades rely on trend confirmation and the weekly levels.

## Run
`python3 pivot_points.py prices.csv --account 10000 --risk 0.01`
Prints next-session and weekly levels, bias, confirmations, setup, and (if everything lines up) entry, stop, shares, half-exit level and trailing stop.
`pivot_points.ts` is a thinkScript study that draws the levels (day or week) on a chart. It is untested in thinkorswim: paste it, check for errors, try in paperMoney.

## With the portfolio
`nightly-plan` calls this skill; a confirmed setup becomes a BUY candidate with its target and partial-exit note in the report. Log simulated trades with `Signal source` = `pivot-points + trend`. Paper-test 100+ signals first. Not investment advice.
