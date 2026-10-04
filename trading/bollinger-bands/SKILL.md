---
name: bollinger-bands
description: Part of the trading skill. Bollinger Bands volatility-breakout strategy on daily/weekly charts for volatile stocks: squeeze detection, long entry on a close above the upper band, stop at the breakout candle low, middle-band trailing stop, and a sideways-market false-signal check. Use when she asks about Bollinger Bands, volatility, squeezes, or breakouts.
---

# Bollinger Bands (volatility breakout)

Analysis and simulated signals only; never place orders.

## The bands
- **Middle** = 20-period simple moving average. **Upper / lower** = middle +/- 2 standard deviations.
- Bands widen when volatility rises and narrow when it falls. Use **daily or weekly** charts only; intraday is rejected.
- Price usually stays inside the bands in quiet periods. A close above the upper band means volatility is expanding.

## Strategy (breakout, long only)
1. **Squeeze**: bandwidth `(upper - lower) / middle` in its lowest 20% of the last 120 bars = coiled market. A breakout right after a squeeze is the best setup.
2. **Entry**: the close breaks above the upper band (a fresh cross, not a stock already running above it).
3. **Stop-loss**: the low of the breakout candle. Report its distance as risk %, and size so the loss is about 1% of the account.
4. **Hold and trail**: carry the position and use the **middle band as a trailing stop**. Exit on a close below it.

## Who it fits
Use it on **volatile** stocks (annualized volatility about 30% or more), because the edge is the stock's ability to break through the upper band. This is the opposite of RSI, which is more reliable on calm, liquid stocks. Calm stocks give breakouts that fizzle; the script flags them.

## Sideways markets (the main weakness)
In a range, price pokes above the upper band and falls back, so breakouts there are mostly false. The script checks ADX: below 20 marks the signal as a likely false one, and it reports historical results for sideways vs trending breakouts so the cost is visible. If ADX is below 20 and there was no squeeze, skip it.

## Run
`python3 bollinger.py prices.csv --account 10000 --risk 0.01`
Prints the bands, bandwidth percentile, squeeze, ADX, volatility, action, stop and size, plus the stock's own history of breakout results split into sideways and trending.

## Do not confuse with mean reversion
Bollinger Bands can also be used to fade the edges (buy at the lower band). That is the mean-reversion skill's job. Here the bands are only used for upside breakouts. Never run both on the same stock at once.

## How it fits the portfolio
It is a volatility flavor of trend following (swing sleeve). Confirm with `trend-identification` (is the breakout out of a base or a downtrend?) and `equity-research` (is there a catalyst or just hype?). RSI above 70 at a breakout is normal in strong trends; don't read it as a sell. Log simulated trades with `Signal source` = `bollinger-bands`. Paper-test 100+ signals first. Not investment advice.
