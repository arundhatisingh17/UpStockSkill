# UpStockSkill

**A set of Claude skills that helps you research stocks, spot trends, and practice trading with fake money before risking real money.**

> **Read this first.** This is an educational tool, not investment advice. It never places trades or touches your brokerage account. Most traders lose money, especially day traders. Practice in a paper (simulated) account first, and only invest money you can afford to lose.

## The big idea

The skill splits a portfolio into two parts:

| Part | Goal | How long you hold | Skills used |
|---|---|---|---|
| **Long-term** (default 60%) | Own good companies and let them grow | Months to years | Equity Research |
| **Swing** (default 40%) | Capture price moves | Days to weeks | Trend Identification, Trend Following, Mean Reversion, RSI, Bollinger Bands, Pivot Points |

The swing part is split again: half uses **trend following** (ride a move) and half uses **mean reversion** (buy a dip that should bounce back). The percentages are just starting points that you can change.

## The skills, in plain English

### 1. Equity Research: "Is this a good company?"
Gathers the facts about a company: how fast sales are growing, how profitable it is, how it compares to rivals, upcoming events, what could go wrong, and a bull/base/bear view of what it might be worth. Every number must come with a source and date; if it can't find something, it says so instead of guessing.
*Use it to decide which stocks are worth watching.*

### 2. Trend Identification (Dow Theory): "Which way is the stock heading?"
Looks at the stock's peaks and valleys:
- **Uptrend:** each high and each low is higher than the one before.
- **Downtrend:** each high and each low is lower than the one before.
- **Sideways:** highs and lows stay at about the same levels.

It also gives simple rules:
- **Sell** when an uptrend breaks: the price makes a lower high, then drops below the last low.
- **Buy** when a downtrend turns: the price makes a higher low, then rises above the last high. Put your **stop-loss** (an automatic exit if the price falls) at that higher low.

*Use it to time when to get in and out.*

### 3. Trend Following: "How strong is the trend, and how much should I buy?"
Rides moves that are already underway. It checks long-term averages, measures trend strength (a number called ADX), and flags a **breakout** when the price pushes above its recent 20-day high. It also sets a stop-loss and tells you how many shares keep your loss to about 1% of your account if you're wrong.
Expect to be wrong more often than right (about 35-45% wins), but winners are bigger than losers.
*Use it when ADX is above 25 (strong trend).*

### 4. Mean Reversion: "Has the stock dropped too far, too fast?"
Prices sometimes overshoot because of panic, then drift back to their average. This skill measures how far below average the price is (a "z-score"), checks that the stock actually tends to bounce back, then flags a buy when it is unusually low (z below -2) and an exit when it returns to normal. If it keeps falling (z below -3), it says to stop out.
It looks at the "average" three ways (simple, exponential and weighted moving averages) and only flags a buy when at least two agree, so one noisy reading doesn't trigger a trade. It also warns if the short-term average is sinking well below the longer one, which can mean a real downtrend is starting.
This is **not risk-free**: a stock that is really starting a long decline keeps falling.
*Use it when ADX is below 20 (no trend).*

### 5. RSI: "Is the stock moving too fast in one direction?"
RSI is a 0-100 gauge of momentum.
- **Below 30 = oversold** (may be due for a bounce). **Crossing above 70 = overbought** (may be due for a pullback).
- **40-60 means sideways, above 60 bullish, below 40 bearish** (a rule of thumb from John Hayden).
- **Divergence:** if the price hits a new high but RSI doesn't, buying momentum is fading (bearish). If the price hits a new low but RSI doesn't, selling momentum is fading (bullish). If the bearish warning keeps repeating in a strong uptrend, it's usually a false alarm, so the skill counts them and tells you not to sell on that alone.
- **Built-in safety checks:** it refuses penny stocks, thinly traded stocks, charts shorter than 120 days, and short 5-10 minute charts. It also asks you to check the news, because a move caused by earnings or hype isn't a normal signal.
RSI is a **second opinion**, never a trade trigger by itself.

### 6. Bollinger Bands: "Is a quiet stock about to make a big move?"
Bollinger Bands draw an upper line, a lower line and a middle line (the 20-day average) around the price. When the bands squeeze tight, the stock is quiet. When the price **closes above the upper band**, volatility is picking up and a run may be starting.
- **Buy** on that breakout. Put your **stop-loss at the low of the breakout day**.
- **Hold** while the price stays above the middle line. **Sell** if it closes below it (a "trailing stop").
- **Best for volatile stocks** (big daily swings), the opposite of RSI, which suits calmer stocks.
- **Biggest risk:** in a sideways market the price pokes above the band and falls right back. The skill checks for this and shows how often the stock's past breakouts failed.

### 7. Pivot Points: "Where are the support and resistance levels?"
Support is a price where many people are willing to buy, and resistance is a price where many are willing to sell. Pivot points turn yesterday's high, low and close into a ladder of levels: a central pivot (PP), three supports below (S1, S2, S3) and three resistances above (R1, R2, R3). If price opens or breaks above R1 it leans up; below S1 it leans down.
The skill looks for two entries, **only in a strong, confirmed uptrend**:
- a **pullback** that dips to a support level and bounces, or
- a **breakout** that closes above resistance.
Then it sets a **stop-loss just below the support**, tells you to **sell about half at the next resistance**, and keep the rest with a **trailing stop at the support** below the price. It skips trades that don't offer at least $1.50 of reward for every $1 risked.
**Important:** pivots come from past prices, so check the news for overnight surprises. They show where price may react, never a buy or sell signal on their own.

### 8. Nightly Plan: "What do I do tomorrow?"
Each evening it reads your positions and recent prices from your Schwab account (**read-only**), runs every skill above, and produces:
- an **order sheet**: for each stock, a decision (buy candidate, hold, or review exit), a limit price, a stop-loss, how many shares to keep your loss near 1% of the account, and notes;
- a **thinkorswim script** (thinkScript) that draws your entry, stop and target lines on the chart and sets alerts.

You review the sheet at night and enter the orders yourself the next day. Be aware that thinkScript **cannot place orders**; it only draws and alerts, and nothing here ever trades for you. The Schwab connection needs your own developer app and keys, which stay on your computer and are never committed to this repo.

### 9. Paper Trading Ledger: "Practice without real money"
A spreadsheet that logs simulated trades, using realistic prices (buy at the ask, sell at the bid), and shows your weekly and compounded returns. Run it for at least 100 trades or a few months before using real funds, and compare yourself to simply holding the S&P 500 (SPY).

## How the skills work together

```
Equity Research  -> picks stocks worth watching
        |
   Which swing strategy fits?  (check ADX)
   ADX > 25  -> Trend Following + Trend Identification
               (volatile stock after a squeeze: Bollinger Bands)
   ADX < 20  -> Mean Reversion
   in between -> wait
        |
RSI (confirmation) -> second opinion on any signal
        |
Nightly Plan -> order sheet + thinkScript for you to review
        |
Paper Trading Ledger -> record and measure the results
```

A stock should pass **both** a business check (Equity Research) and a timing check (a trend or mean-reversion signal) before you act.

## Quick start

1. Install [Claude Code](https://claude.ai/claude-code) and copy the `trading/` folder into `~/.claude/skills/`.
2. Ask Claude things like:
   - "Research AAPL"
   - "What trend is NVDA in?"
   - "Is MSFT oversold? Does it bounce back?"
3. For the code tools, save a stock's daily prices as a CSV (columns: `date, high, low, close`) and run:
   ```bash
   python3 trading/trend-identification/trend_detector.py prices.csv
   python3 trading/trend-following/trend_following.py prices.csv
   python3 trading/mean-reversion/mean_reversion.py prices.csv
   python3 trading/rsi/rsi.py prices.csv --catalyst no
   python3 trading/bollinger-bands/bollinger.py prices.csv
   python3 trading/pivot-points/pivot_points.py prices.csv
   python3 trading/nightly-plan/nightly_plan.py --csv-dir ./prices --watchlist AAPL,MSFT
   ```
   These need Python with `pandas` and `numpy`.
4. Log the trades in the paper ledger (`python3 paper-trading/build_ledger.py` creates it).

## Limits you should know
- Signals lag: they confirm a turn after it happens, and sideways markets cause false alarms.
- Paper results look better than real trading, because real fills are worse.
- One good month proves very little. Look at 100+ trades and your worst losing streak.
- If you are on a student or work visa, check whether frequent trading affects your status.

## What's inside
```
trading/
  SKILL.md                    main skill and portfolio rules
  equity-research/            fundamentals
  trend-identification/       Dow Theory + trend_detector.py
  trend-following/            trend strength + trend_following.py
  mean-reversion/             dip buying + mean_reversion.py
  rsi/                        momentum gauge + rsi.py
  bollinger-bands/            volatility breakouts + bollinger.py
  pivot-points/               support/resistance + pivot_points.py
  nightly-plan/               order sheet + thinkScript + nightly_plan.py
paper-trading/build_ledger.py simulated-trade spreadsheet
```
