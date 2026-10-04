# UpStockSkill

A Claude skill for stock trading research on Charles Schwab / thinkorswim. It prepares and analyzes; it never places orders.

## Commit log
- **Commit 2**: Trading skill that builds trade plans, thinkorswim order tickets and thinkScript, and simulates long-term stock trades in a paper-trading ledger (weekly compounded return vs SPY).
- **Commit 3**: Added trend-identification sub-skill that classifies uptrends, downtrends and sideways markets with Dow Theory swing highs/lows and emits BUY (stop at the higher low), SELL and STOP signals.
- **Commit 4**: Added equity-research sub-skill (adapted from quant-sentiment-ai/claude-equity-research, MIT) for sourced fundamental reports, to be used with trend-identification: fundamentals pick what to watch, Dow Theory times entries and exits.
