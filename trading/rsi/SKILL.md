---
name: rsi
description: Part of the trading skill. Relative Strength Index (RSI) on daily/weekly stock charts: oversold/overbought signals, John Hayden 40/60 regime, bullish/bearish divergences with a frequency check, plus guardrails against penny stocks, illiquid names, jumpy prices, short windows, intraday charts and catalyst-driven moves. Use when she asks about RSI, oversold/overbought, momentum, or divergences.
---

# RSI (momentum oscillator)

Analysis and simulated signals only; never place orders. RSI moves between 0 and 100 (Wilder, 14 periods).

## Signals
- **Below 30 = oversold**: BUY candidate.
- **Crosses above 70 = overbought**: SELL candidate. (Already above 70 with no fresh cross is "overbought", not a new signal.)
- **John Hayden regime**: RSI above 60 bullish, below 40 bearish, 40-60 sideways. In a bullish regime RSI often stays above 70; do not treat every 70 as a top.

## Divergences (momentum vs price)
- **Bearish**: price makes a new high but RSI makes a lower high. Momentum is shifting against buyers.
- **Bullish**: price makes a new low but RSI makes a higher low. Momentum is turning up.
- Divergences are early hints, not predictions. Always confirm with another indicator.
- **Frequency check**: count bearish divergences over the last ~60 bars. Two or more usually means a strong trend, and RSI keeps flagging a top that never comes. Do NOT sell or short on repeated bearish divergences alone.

## Limits and guardrails (all enforced by `rsi.py`)
- **Timeframe**: daily or weekly only. Never use it on 5-10 minute charts; too noisy. Intraday data is rejected.
- **Window**: at least 120 bars, or the RSI is unreliable.
- **No penny or illiquid stocks**: reject price under $5, market cap under $300M, or average volume under 500k shares. Ask for market cap and volume; if unknown, flag it.
- **Jumpy prices** (gaps, spikes) distort RSI. The script warns when one move exceeds 15% or several exceed 4 standard deviations.
- **Organic moves only**: before acting, run a news and sentiment check (web search for earnings, guidance, FDA/legal news, upgrades/downgrades, social-media hype, via `equity-research`). If a catalyst explains the move, the signal is "not organic": do not act. There is no automated sentiment analyzer here; this check is manual, so pass `--catalyst yes|no`. Until it is checked the script prints a flag.

## Run
`python3 rsi.py prices.csv --market-cap 5e9 --avg-volume 2e6 --catalyst no`
Prints price, RSI, zone, Hayden regime, signal, divergence note, flags.

## How it fits the portfolio
Use as a **confirmation layer**, not a standalone trigger:
- With `mean-reversion`: RSI < 30 plus z-score <= -2 plus a reverting stock is a stronger dip-buy.
- With `trend-following` / `trend-identification`: in an uptrend, RSI dipping to 40-50 is a pullback entry, not a sell; a bearish divergence near a Dow Theory lower high adds weight to an exit.
- Log simulated trades in the ledger with `Signal source` = `rsi + <other skill>`. Paper-test 100+ signals first. Not investment advice.
