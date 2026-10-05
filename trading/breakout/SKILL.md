---
name: breakout
description: Part of the trading skill. Decides whether a breakout candle is genuine or false with four tests (big candle, fresh cross, no upper wick, volume) plus a smooth-chart filter, and lays out the book's execution plan (buy-stop above the high, stop at the low, day-after trail, 75/25 exit). Use when she asks about a breakout candle, a false or failed breakout, whether a breakout is real, follow-through after a breakout, trailing a breakout stop, or a partial exit / runner.
---

# Breakout quality (genuine vs false)

Analysis and simulated signals only; never place orders. Rules adapted from Indrazith Shantharaj, *How to Make Money with Breakout Trading* (2020). Daily charts only; long only.

## Idea
A close above a line is not a breakout. Smart money buying at resistance leaves a signature on the candle itself: it is **big**, it is a **fresh** cross, it closes near its high with **no upper wick**, and it carries **volume**. False breakouts fail at least one of these because sellers showed up at the level.

## Four tests, all on the breakout candle
| Test | Rule | What it catches |
|---|---|---|
| `big` | range >= 1.5 x ATR(14) | an ordinary day that drifted over the line |
| `fresh` | close > level and the 3 prior closes were not | a stock already running above the level |
| `no_wick` | (high - close) / range < 20% | sellers pushed it back before the close |
| `volume` | >= 1.5 x the 20-day average | a move with no size behind it |

Book example for `no_wick`: low 100, high 110, so the close must be above 108.
`volume` is reported as unknown when the CSV has no volume column. **Genuine** means all four known tests pass. Anything less is reported as "n/4 tests, failed ..." so the failing test is named.

## Chart filter (before the candle)
`smooth()` rejects charts with more than 6 gaps over 3% in 120 bars or an average upper wick above 45% of range (a normal bar averages 25 to 30%). Both thresholds are knobs, set from the book's examples, not from a backtest. Gappy, wicky or thinly traded "operator" charts jump through stops and entries at random, so the candle tests cannot be trusted on them.

## Execution plan (what the book does after a pass)
- **Entry**: buy-stop a few ticks above the breakout candle high. The market confirms by trading higher; a limit below the close would be buying a pullback, the opposite idea. Skip if it opens more than 2% above that high, even if it comes back.
- **Stop**: a few ticks below the breakout candle low. Size so the stop-out is about 1% of the account.
- **Target**: out of a downtrend, the prior top; out of a range, the range width projected up; at all-time highs, none (manage by trail). Take the trade only at 1:2 or better.
- **Follow-through** (days 1 to 3): if the next candle is small, a doji or red, raise the stop to that day's low. Most failures become roughly breakeven.
- **Runner**: exit 75% at target, trail the last 25% below each swing low.
- **Caps**: at most 10% of capital per trade, 5 open positions, 50% deployed, 2 to 3 new ideas a night.

## Run
`python3 breakout.py prices.csv [--level 123.45] [--account 10000] [--risk 0.01]`
Prints the chart filter, the four tests with their measurements, and the execution plan if every test passed. CSV columns: `date, high, low, close`, plus `open` and `volume` for the gap and volume tests.

## Status in the nightly plan
`nightly-plan` runs `quality()` and `smooth()` on every symbol with a breakout path, and on any symbol that closed above its prior 20-day high, and shows the result as a **flag** in the notes and the Discord digest. It does not yet gate the candidate, change the entry to a buy-stop, trail the stop, split the exit or apply the caps. Run it this way for a few weeks, compare flagged against unflagged outcomes in the paper ledger, then decide what to enforce.

## With the other skills
`bollinger-bands` and `trend-following` supply the trigger; this skill judges the candle. `trend-identification` says whether the break is out of a downtrend, a range or at new highs, which sets the target. `pivot-points` gives the next resistance for a target. Log simulated trades with `Signal source` = `breakout + <trigger skill>`. Paper-test 100+ signals first. Not investment advice.
