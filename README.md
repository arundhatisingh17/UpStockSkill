# UpStockSkill

**A set of Claude skills that helps you research stocks, spot trends, and practice trading with fake money before risking real money.**

> **Read this first.** This is an educational tool, not investment advice. It never places trades or touches your brokerage account. Most traders lose money, especially day traders. Practice in a paper (simulated) account first, and only invest money you can afford to lose.

## The big idea

The skill splits a portfolio into two parts:

| Part | Goal | How long you hold | Skills used |
|---|---|---|---|
| **Long-term** (default 60%) | Own good companies and let them grow | Months to years | Equity Research |
| **Swing** (default 40%) | Capture price moves | Days to weeks | Trend Identification, Trend Following, Mean Reversion |

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
This is **not risk-free**: a stock that is really starting a long decline keeps falling.
*Use it when ADX is below 20 (no trend).*

### 5. Paper Trading Ledger: "Practice without real money"
A spreadsheet that logs simulated trades, using realistic prices (buy at the ask, sell at the bid), and shows your weekly and compounded returns. Run it for at least 100 trades or a few months before using real funds, and compare yourself to simply holding the S&P 500 (SPY).

## How the skills work together

```
Equity Research  -> picks stocks worth watching
        |
   Which swing strategy fits?  (check ADX)
   ADX > 25  -> Trend Following + Trend Identification
   ADX < 20  -> Mean Reversion
   in between -> wait
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
paper-trading/build_ledger.py simulated-trade spreadsheet
```
