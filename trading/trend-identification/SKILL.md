---
name: trend-identification
description: Part of the trading skill. Classifies a stock's trend as uptrend, downtrend, sideways, or transition using Dow Theory swing structure (higher/lower highs and lows), and surfaces BUY/SELL/STOP signals for the paper-trading ledger. Use when she asks what trend a stock is in, whether an uptrend has ended, or when to enter/exit on a trend change.
---

# Trend identification (Dow Theory swing structure)

Analysis and simulated signals only. Never place real orders; if she holds the stock, tell her the rule has triggered and let her act. Log simulated trades in `paper-trading/paper_ledger.xlsx`.

## Definitions (swing highs/lows, confirmed on closes)
- **Uptrend**: higher highs (HH) and higher lows (HL).
- **Downtrend**: lower highs (LH) and lower lows (LL).
- **Sideways**: highs and lows about the same, within a tolerance (default 1%).
- **Mixed/transition**: e.g. HH with LL. Wait; do not act.
- A swing high/low is the extreme over `n` bars on each side (default 3). It is only known `n` bars later, so never use an unconfirmed swing.

## Rules
1. **End of uptrend / SELL**: a lower high forms, then a lower low. The close below the last swing low is the signal. If she holds the stock, flag it for sale at once, since the rule says to exit at the onset of the downtrend.
2. **End of downtrend / BUY**: a higher low forms, then a higher high. The close above the last swing high is the entry. Put the **stop-loss at the higher low**.
3. **STOP**: a close below the stop level exits the position.

## How to run
`python3 trend_detector.py prices.csv --n 3 --tol 0.01` (CSV columns: date, high, low, close). It prints the current trend and the BUY/SELL/STOP events. Get prices from `yfinance` or Schwab market data (read-only).

## Report format
Ticker, current trend, last two swing highs and lows (with dates), signal (if any), entry/stop, and the paper-ledger row to add. Use daily bars by default; mention if the timeframe changes the answer (weekly vs daily).

## Dow Theory caveats to state
- Classic Dow Theory also wants **volume confirmation** and **confirmation from a second index** (e.g. Dow Industrials plus Transports, or S&P plus Nasdaq). This detector uses price structure only; say so.
- It lags: a swing needs `n` bars to confirm, so entries and exits come after the turn. Whipsaws in sideways markets are common; the tolerance and `n` are tuning knobs, and tuning on the same data is overfitting.
- Check the signal on the chart in thinkorswim before relying on it. Paper-test over 100+ signals before using real money. Not investment advice.
