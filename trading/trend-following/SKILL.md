---
name: trend-following
description: Part of the trading skill. Swing-trading "trend following" sleeve: measures trend direction and strength (moving averages, ADX), gives breakout entries, exits, ATR stops and position size. Use when she asks whether a stock is trending, how strong the trend is, or for a trend-based entry/exit. Pairs with trend-identification (Dow Theory).
---

# Trend following (swing sleeve)

Analysis and simulated signals only; never place orders. Concepts inspired by common CTA/Turtle-style trend systems; written independently for stocks.

## Idea
Prices that are moving tend to keep moving for a while. Buy strength, hold while the trend lasts, exit when it breaks. Expect a low win rate (~35-45%) with winners bigger than losers.

## Rules
- **Trend filter**: price above the 200-day average and the 50-day above the 200-day = uptrend.
- **Strength (ADX 14)**: above 25 strong; 20-25 developing; below 20 no trend (use mean-reversion instead or stay out).
- **Entry**: close above the 20-day high, only when the filter says uptrend.
- **Exit**: close below the 10-day low, or below the stop.
- **Stop**: entry minus 2 x ATR(14).
- **Size**: shares = (account x risk%) / (2 x ATR). Default risk 1% of account per trade.
- Long only unless she confirms a margin account and wants shorts.

## Run
`python3 trend_following.py prices.csv --account 10000 --risk 0.01`
Prints trend, ADX, which strategy fits, action, stop, and shares.

## With Dow Theory
Take a trade only when this skill AND `trend-identification` agree on an uptrend. If they disagree, wait. Log simulated trades in the paper ledger with `Signal source` = `trend-following`.

## Caveats
Whipsaws in sideways markets are the main cost; the ADX filter reduces but cannot remove them. Slow systems lag. Test 100+ signals in paper before real money. Not investment advice.
