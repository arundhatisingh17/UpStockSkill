---
name: mean-reversion
description: Part of the trading skill. Swing-trading "mean reversion" sleeve: tests whether a stock tends to snap back to its average, measures how stretched it is (z-score), and gives buy/exit/stop signals. Use when she asks about oversold/overbought stocks, buying dips, pairs/spreads, or whether a sideways stock is tradable.
---

# Mean reversion (swing sleeve)

Analysis and simulated signals only; never place orders. Concepts (z-score, half-life, Hurst, variance ratio) follow standard quant practice; written independently for stocks.

## How it makes money
Prices sometimes overshoot because of panic or hype, then drift back toward their average. The strategy buys when price is unusually far below its average and sells when it returns. The "anomaly" is the temporary gap. It is statistical, not risk-free arbitrage: if the stock is really starting a new downtrend, the gap keeps widening.

## Step 1: does this stock revert at all?
- **Hurst exponent** below 0.5 = reverting; 0.5 = random; above 0.5 = trending.
- **Half-life**: days for a gap to halve. Use only if roughly 2-60 days. Lookback is about 2x half-life; max hold about 3x.
- **Variance ratio** below 1 supports reversion.
- The script requires Hurst < 0.5 and a sane half-life. Hurst alone can mislead on drifting stocks, so the half-life check is a second gate.

## Step 2: how stretched is it?
`z = (price - rolling mean) / rolling std` (default 20 days). The "mean" can be defined three ways (`--mean sma|ema|wma`, default sma):
- **SMA**: plain average, every day weighted equally. Slowest and smoothest.
- **EMA**: recent days weighted more (exponentially). Reacts faster, noisier.
- **WMA**: recent days weighted more (linearly). In between.
The script prints all three z-scores. These are the same prices seen three ways, not three independent confirmations. A buy needs z <= -2 AND at least 2 of the 3 averages agreeing; if only the fast EMA is stretched, treat it as noise.
`ema_vs_sma_gap_pct` is a speed check: if the EMA sits well below the SMA (gap under about -1.5%, `trend_warning`), a downtrend may be developing and the dip may not revert.
Moving averages describe where price has been; they do not predict anomalies. The Hurst/half-life gate in Step 1 is what decides if reversion is plausible.

## Step 3: rules (long only)
- z <= -2: **BUY** signal.
- z back near 0 (the average): **exit**.
- z <= -3: **stop**, reversion is failing.
- Time stop: exit after 3x half-life if it has not reverted.
- Short side and pairs trades need a margin account; mention and skip unless she asks.

## Run
`python3 mean_reversion.py prices.csv --lookback 20 --mean sma`
Prints Hurst, half-life, variance ratio, the SMA/EMA/WMA z-scores, trend warning, whether it reverts, action and the target exit (the mean).

## When not to use
Strong trends (use trend-following), earnings or news shocks, low-liquidity stocks with wide spreads, and regime changes. Use ADX < 20 as the green light; ADX > 25 means stand aside.

## With the other skills
Only trade a dip if `equity-research` says the business is sound; a cheap stock with broken fundamentals is a falling knife. Log simulated trades with `Signal source` = `mean-reversion`. Paper-test 100+ signals first. Not investment advice.
